"""feat-009 — run the full feat-001..feat-007 pipeline once, offline, over a
real document set and save the static output so the live demo doesn't depend
on Fireworks/Gemma latency or availability during judging.

See docs/concept-graph-pipeline.md for the 6-step pipeline this composes
(chunk -> extract concepts -> cluster -> infer prerequisites -> validate ->
assign levels), plus feat-007's per-node lesson/quiz/example generation. All
of the actual logic already lives in packages/gpu-worker and apps/api and is
unit-tested there; this script only orchestrates it end to end and writes
the combined result to disk.

Requires a real local Gemma/Ollama server (GEMMA_BASE_URL) and a real
Fireworks API key (FIREWORKS_API_KEY) — this script performs the one real,
ahead-of-time LLM pass that feat-009 exists to precompute; it deliberately
refuses to run with fakes substituted in, since a fake-LLM placeholder
pretending to be real pipeline output is exactly what feat-009 replaces. For
a version exercised with fakes (to verify this script's own orchestration
logic, not the pipeline's judgment calls), see scripts/tests/test_build_demo_dataset.py.

Prototyping-only alternative: set LLM_PROVIDER=openai and OPENAI_API_KEY to
run this same pipeline against GPT-4o mini + text-embedding-3-small instead,
to validate the wiring before real ROCm/Gemma/Fireworks infra exists (see
docs/hackathon-scope.md §5). If doing so, also consider raising
--prereq-similarity-threshold (try 0.6) — the 0.35 default was implicitly
tuned for bge-large-en-v1.5's cosine-similarity distribution, and a live run
found it lets through ~6x more candidate pairs than expected against
OpenAI's text-embedding-3-small, which is correct but needlessly slow/costly.

Usage:
    GEMMA_BASE_URL=http://localhost:11434 FIREWORKS_API_KEY=... \\
        python scripts/build_demo_dataset.py

    # or, prototyping against OpenAI:
    LLM_PROVIDER=openai OPENAI_API_KEY=... \\
        python scripts/build_demo_dataset.py --prereq-similarity-threshold 0.6
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "packages" / "gpu-worker"))
sys.path.insert(0, str(_REPO_ROOT / "apps" / "api"))

from worker.concepts import (  # noqa: E402
    GemmaConceptExtractor,
    OpenAIConceptExtractor,
    OpenAIEmbedder,
    SentenceTransformerEmbedder,
    cluster_concepts,
    extract_raw_concepts,
)
from worker.ingest import Chunk, chunk_document  # noqa: E402
from worker.prerequisites import FireworksClient as PrerequisiteFireworksClient  # noqa: E402
from worker.prerequisites import build_candidate_edges  # noqa: E402

from app.services.graph import validate_graph  # noqa: E402
from app.services.levels import assign_levels  # noqa: E402
from app.services.teach import FireworksClient as TeachFireworksClient  # noqa: E402
from app.services.teach import generate_lesson_package  # noqa: E402

_DEFAULT_DOCS_DIR = _REPO_ROOT / "data" / "source_docs"
_DEFAULT_OUTPUT = _REPO_ROOT / "data" / "generated" / "demo_tree.generated.json"
_EMPTY_LESSON_PACKAGE = {
    "lesson": "",
    "quiz": {"question": "", "options": [], "answer_index": 0},
    "questions": [],
    "example": "",
    "sources": [],
    "self_check": {"passed": False, "attempts": 0},
    "pass_threshold": 0.6,
}


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# IMP-C2: gamification metadata helpers
_DIFFICULTY_BADGE = {
    "foundational": "⭐ Foundational",
    "intermediate": "⭐⭐ Intermediate",
    "advanced": "⭐⭐⭐ Advanced",
}
_LEVEL_XP = {0: 50, 1: 100, 2: 150}  # XP increases with depth
_LEVEL_MINUTES = {0: 10, 1: 15, 2: 20}  # estimated study time per level


def _xp_reward(level: int) -> int:
    """IMP-C2: XP reward scales with level — deeper concepts are worth more."""
    return _LEVEL_XP.get(level, 150 + (level - 2) * 25)


def _estimated_minutes(level: int) -> int:
    """IMP-C2: estimated study time scales with level."""
    return _LEVEL_MINUTES.get(level, 20 + (level - 2) * 5)


def build_dataset(
    chunks: list[Chunk],
    topic: str,
    gemma,
    embedder,
    fireworks_infer,
    fireworks_teach,
    prereq_similarity_threshold: float = 0.35,
    dedup_percentile: float = 99.5,
    min_depth_warn: int = 3,
) -> dict:
    """Compose feat-001's chunks[] through feat-007's per-node lesson
    packages into one final tree JSON, matching the schema in
    docs/concept-graph-pipeline.md. Every step here calls the same,
    already-unit-tested functions the live services use — this function
    only assembles their outputs.

    prereq_similarity_threshold's default (0.35) was implicitly tuned for
    bge-large-en-v1.5's cosine-similarity distribution — a live run found
    it lets through far more candidate pairs than expected against OpenAI's
    text-embedding-3-small (17% of all possible pairs vs. a handful),
    correct but needlessly slow/costly. Pass a higher value (e.g. 0.6) when
    using an embedding backend this wasn't tuned for.

    dedup_percentile controls the adaptive threshold for clustering (IMP-3.3):
    similarity_threshold=None causes cluster_concepts() to compute the threshold
    from the P`dedup_percentile` of the embedding distribution, making it
    model-agnostic. Default 95.0 = top 5% most-similar pairs are near-duplicates.

    min_depth_warn (IMP-D2): if the generated tree has fewer levels than this,
    a warning is printed with suggestions for tuning the pipeline.
    """
    print(f"\n[Step 1] Received {len(chunks)} chunks from source documents.")
    print("[Step 2] Extracting raw concepts via LLM (now with difficulty signals)...")
    raw_concepts = extract_raw_concepts(chunks, gemma)
    print(f"  -> Extracted {len(raw_concepts)} raw concepts.")

    # IMP-A1 diagnostic: difficulty distribution
    diff_counts: dict[str, int] = {}
    for rc in raw_concepts:
        diff_counts[rc.difficulty] = diff_counts.get(rc.difficulty, 0) + 1
    print(f"  -> Difficulty distribution: {diff_counts}")

    print(f"[Step 3] Clustering and deduping concepts (adaptive P{dedup_percentile} threshold)...")
    canonical_concepts = cluster_concepts(raw_concepts, embedder, dedup_percentile=dedup_percentile)
    concept_dicts = [concept.to_dict() for concept in canonical_concepts]
    print(f"  -> Reduced to {len(concept_dicts)} canonical concepts.")

    print("[Step 4] Inferring prerequisite edges via LLM (all-pairs for small datasets)...")
    candidate_edges = build_candidate_edges(
        concept_dicts, fireworks_infer, similarity_threshold=prereq_similarity_threshold
    )
    print(f"  -> Found {len(candidate_edges)} candidate edges.")

    print("[Step 5] Validating DAG (cycle detection)...")
    validated = validate_graph(candidate_edges)
    print(f"  -> Dropped {len(validated['dropped_edges'])} edges to fix cycles. Valid edges: {len(validated['edges'])}.")

    print("[Step 6] Assigning concept tiers/levels...")
    leveled_nodes = assign_levels(validated["edges"], concept_dicts)

    # IMP-D2: warn if tree is too shallow
    max_level = max((n["level"] for n in leveled_nodes), default=0)
    if max_level < min_depth_warn:
        print(
            f"\n[WARNING] Tree depth is only {max_level + 1} level(s) — expected at least {min_depth_warn}.\n"
            f"  This usually means Step 4 produced too few edges. Try:\n"
            f"  • Lowering --prereq-similarity-threshold (current: {prereq_similarity_threshold})\n"
            f"  • Checking that source documents contain varied difficulty levels\n"
            f"  • Running with PREREQ_MAX_ALL_PAIRS env var set higher\n"
        )

    print("[Step 7] Generating lessons, examples, and quizzes for each node via LLM (this may take a while)...")

    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    prerequisites_by_id: dict[str, list[str]] = {node["id"]: [] for node in leveled_nodes}
    for edge in validated["edges"]:
        prerequisites_by_id.setdefault(edge["to"], []).append(edge["from"])

    # Build a name lookup for IMP-B3 prerequisite context
    name_by_id = {c["id"]: c["name"] for c in concept_dicts}

    nodes = []
    for leveled in leveled_nodes:
        node_chunks = [
            {
                "chunk_id": chunk_id,
                "doc_id": chunks_by_id[chunk_id].doc_id,
                "page": chunks_by_id[chunk_id].page,
                "text": chunks_by_id[chunk_id].text,
            }
            for source in leveled["sources"]
            if (chunk_id := source["chunk_id"]) in chunks_by_id
        ]

        # IMP-B3: pass prerequisite names for context-aware lesson generation
        prereq_ids = prerequisites_by_id.get(leveled["id"], [])
        prereq_names = [name_by_id[pid] for pid in prereq_ids if pid in name_by_id]

        node_level = leveled["level"]
        package = (
            generate_lesson_package(
                leveled["name"],
                node_chunks,
                fireworks_teach,
                prerequisite_names=prereq_names,  # IMP-B3
                node_level=node_level,             # IMP-B2 pass_threshold
            )
            if node_chunks
            else _EMPTY_LESSON_PACKAGE
        )

        node_id = leveled["id"]

        # IMP-B2: build multi-question quiz structure
        all_questions = package.get("questions", [])
        # Fallback to legacy single-question if LLM returned old format
        if not all_questions and package.get("quiz", {}).get("question"):
            legacy_q = package["quiz"]
            all_questions = [{"difficulty": "medium", **legacy_q}]

        # Assign unique IDs to each question
        questions_with_ids = [
            {
                "id": f"q_{node_id}_{idx + 1}",
                "type": "mcq",
                "difficulty": q.get("difficulty", "medium"),
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "answer_index": q.get("answer_index", 0),
            }
            for idx, q in enumerate(all_questions)
            if q.get("question")
        ]

        # IMP-C2: gamification fields
        node_difficulty = leveled.get("difficulty", "intermediate")  # from concept_dict if available
        # Try to get difficulty from concept_dict
        concept_for_node = next((c for c in concept_dicts if c["id"] == node_id), {})
        node_difficulty = concept_for_node.get("difficulty", "intermediate")

        nodes.append(
            {
                "id": node_id,
                "title": leveled["name"],
                "concept_key": _slugify(leveled["name"]),
                "level": node_level,
                "difficulty": node_difficulty,                        # IMP-A1
                "difficulty_badge": _DIFFICULTY_BADGE.get(node_difficulty, "⭐ Unknown"),  # IMP-C2
                "xp_reward": _xp_reward(node_level),                 # IMP-C2
                "estimated_minutes": _estimated_minutes(node_level),  # IMP-C2
                "status": leveled["status"],
                "prerequisites": prereq_ids,
                "lesson": {
                    "summary": package.get("lesson", ""),
                    "real_world_example": package.get("example", ""),
                },
                "quiz": {
                    "id": f"q_{node_id}",
                    "pass_threshold": package.get("pass_threshold", 0.7),  # IMP-B2 level-aware
                    "questions": questions_with_ids,
                },
                "sources": [
                    {"doc_id": source["doc_id"], "page": source.get("page")} for source in package.get("sources", [])
                ],
            }
        )

    edges = [{"from": edge["from"], "to": edge["to"]} for edge in validated["edges"]]
    tier0_ids = [node["id"] for node in nodes if node["level"] == 0]
    locked_ids = [node["id"] for node in nodes if node["level"] > 0]

    return {
        "topic": topic,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "nodes": nodes,
        "edges": edges,
        "dropped_edges": validated["dropped_edges"],
        "user_progress": {
            "completed_nodes": [],
            "unlocked_nodes": tier0_ids,
            "locked_nodes": locked_ids,
            "total_nodes": len(nodes),
            "percent_complete": 0,
        },
        "tree_stats": {  # IMP-D2 diagnostic
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "max_depth": max_level,
            "difficulty_distribution": {
                lvl: sum(1 for n in nodes if n.get("difficulty") == lvl)
                for lvl in ("foundational", "intermediate", "advanced")
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs-dir", default=str(_DEFAULT_DOCS_DIR), help="Directory of PDF/PPTX/DOCX source docs")
    parser.add_argument("--topic", default="Introduction to Machine Learning")
    parser.add_argument("--output", default=str(_DEFAULT_OUTPUT))
    parser.add_argument(
        "--prereq-similarity-threshold",
        type=float,
        default=0.35,
        help="See build_dataset()'s docstring — try 0.6 when using LLM_PROVIDER=openai.",
    )
    parser.add_argument(
        "--dedup-percentile",
        type=float,
        default=99.5,
        help=(
            "Percentile of the embedding similarity distribution used as the dedup"
            " threshold in Step 3 (IMP-3.3). P99.5 (default) = top 0.5%% most-similar"
            " pairs are treated as near-duplicates. Decrease to merge more aggressively;"
            " increase to be more conservative. Model-agnostic by design."
        ),
    )
    parser.add_argument(
        "--min-depth-warn",
        type=int,
        default=3,
        help=(
            "IMP-D2: print a warning if the generated tree has fewer levels than this."
            " Default 3. Set to 0 to disable."
        ),
    )
    args = parser.parse_args()

    use_openai = os.environ.get("LLM_PROVIDER", "").lower() == "openai"

    if use_openai:
        if not os.environ.get("OPENAI_API_KEY"):
            raise SystemExit(
                "LLM_PROVIDER=openai but OPENAI_API_KEY is not set. Refusing to "
                "substitute fake output for the real run."
            )
        gemma = OpenAIConceptExtractor()
        embedder = OpenAIEmbedder()
        fireworks_infer = PrerequisiteFireworksClient()
        fireworks_teach = TeachFireworksClient()
    else:
        gemma_base_url = os.environ.get("GEMMA_BASE_URL")
        fireworks_api_key = os.environ.get("FIREWORKS_API_KEY")
        if not gemma_base_url:
            raise SystemExit(
                "GEMMA_BASE_URL is not set. This script needs a real local Gemma/Ollama "
                "server for concept extraction (docs/hackathon-scope.md §5) — refusing to "
                "substitute fake output, since feat-009 exists to replace a hand-written "
                "placeholder, not produce a different kind of one. (Set LLM_PROVIDER=openai "
                "instead to prototype against GPT-4o mini — see this script's docstring.)"
            )
        if not fireworks_api_key:
            raise SystemExit(
                "FIREWORKS_API_KEY is not set. Required for prerequisite inference "
                "(step 4) and lesson/quiz/example generation (step 7) — refusing to "
                "substitute fake output."
            )
        gemma = GemmaConceptExtractor(base_url=gemma_base_url)
        embedder = SentenceTransformerEmbedder()
        fireworks_infer = PrerequisiteFireworksClient(api_key=fireworks_api_key)
        fireworks_teach = TeachFireworksClient(api_key=fireworks_api_key)

    docs_dir = Path(args.docs_dir)
    chunks: list[Chunk] = []
    for doc_path in sorted(docs_dir.iterdir()):
        chunks.extend(chunk_document(doc_path.name, doc_path.read_bytes()))
    if not chunks:
        raise SystemExit(f"No chunks produced from {docs_dir} — is it empty or missing supported files?")

    dataset = build_dataset(
        chunks,
        topic=args.topic,
        gemma=gemma,
        embedder=embedder,
        fireworks_infer=fireworks_infer,
        fireworks_teach=fireworks_teach,
        prereq_similarity_threshold=args.prereq_similarity_threshold,
        dedup_percentile=args.dedup_percentile,
        min_depth_warn=args.min_depth_warn,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    stats = dataset.get("tree_stats", {})
    print(
        f"\nWrote {stats.get('total_nodes', len(dataset['nodes']))} nodes / "
        f"{stats.get('total_edges', len(dataset['edges']))} edges "
        f"(depth={stats.get('max_depth', '?')}) to {output_path}"
    )
    print(f"Difficulty distribution: {stats.get('difficulty_distribution', {})}")


if __name__ == "__main__":
    main()

# python scripts/build_demo_dataset.py --prereq-similarity-threshold 0.6
