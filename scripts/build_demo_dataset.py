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

Usage:
    GEMMA_BASE_URL=http://localhost:11434 FIREWORKS_API_KEY=... \\
        python scripts/build_demo_dataset.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "packages" / "gpu-worker"))
sys.path.insert(0, str(_REPO_ROOT / "apps" / "api"))

from worker.concepts import (  # noqa: E402
    GemmaConceptExtractor,
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
    "example": "",
    "sources": [],
    "self_check": {"passed": False, "attempts": 0},
}


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def build_dataset(
    chunks: list[Chunk],
    topic: str,
    gemma,
    embedder,
    fireworks_infer,
    fireworks_teach,
) -> dict:
    """Compose feat-001's chunks[] through feat-007's per-node lesson
    packages into one final tree JSON, matching the schema in
    docs/concept-graph-pipeline.md. Every step here calls the same,
    already-unit-tested functions the live services use — this function
    only assembles their outputs."""
    raw_concepts = extract_raw_concepts(chunks, gemma)
    canonical_concepts = cluster_concepts(raw_concepts, embedder)
    concept_dicts = [concept.to_dict() for concept in canonical_concepts]

    candidate_edges = build_candidate_edges(concept_dicts, fireworks_infer)
    validated = validate_graph(candidate_edges)
    leveled_nodes = assign_levels(validated["edges"], concept_dicts)

    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    prerequisites_by_id: dict[str, list[str]] = {node["id"]: [] for node in leveled_nodes}
    for edge in validated["edges"]:
        prerequisites_by_id.setdefault(edge["to"], []).append(edge["from"])

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
        package = (
            generate_lesson_package(leveled["name"], node_chunks, fireworks_teach)
            if node_chunks
            else _EMPTY_LESSON_PACKAGE
        )
        quiz_question = package["quiz"]
        node_id = leveled["id"]
        nodes.append(
            {
                "id": node_id,
                "title": leveled["name"],
                "concept_key": _slugify(leveled["name"]),
                "level": leveled["level"],
                "status": leveled["status"],
                "prerequisites": prerequisites_by_id.get(node_id, []),
                "lesson": {
                    "summary": package["lesson"],
                    "real_world_example": package["example"],
                },
                "quiz": {
                    "id": f"q_{node_id}",
                    "pass_threshold": 0.7,
                    "questions": (
                        [
                            {
                                "id": f"q_{node_id}_1",
                                "type": "mcq",
                                "question": quiz_question["question"],
                                "options": quiz_question["options"],
                                "answer_index": quiz_question["answer_index"],
                            }
                        ]
                        if quiz_question.get("question")
                        else []
                    ),
                },
                "sources": [
                    {"doc_id": source["doc_id"], "page": source.get("page")} for source in package["sources"]
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
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs-dir", default=str(_DEFAULT_DOCS_DIR), help="Directory of PDF/PPTX/DOCX source docs")
    parser.add_argument("--topic", default="Introduction to Machine Learning")
    parser.add_argument("--output", default=str(_DEFAULT_OUTPUT))
    args = parser.parse_args()

    import os

    gemma_base_url = os.environ.get("GEMMA_BASE_URL")
    fireworks_api_key = os.environ.get("FIREWORKS_API_KEY")
    if not gemma_base_url:
        raise SystemExit(
            "GEMMA_BASE_URL is not set. This script needs a real local Gemma/Ollama "
            "server for concept extraction (docs/hackathon-scope.md §5) — refusing to "
            "substitute fake output, since feat-009 exists to replace a hand-written "
            "placeholder, not produce a different kind of one."
        )
    if not fireworks_api_key:
        raise SystemExit(
            "FIREWORKS_API_KEY is not set. Required for prerequisite inference "
            "(step 4) and lesson/quiz/example generation (step 7) — refusing to "
            "substitute fake output."
        )

    docs_dir = Path(args.docs_dir)
    chunks: list[Chunk] = []
    for doc_path in sorted(docs_dir.iterdir()):
        chunks.extend(chunk_document(doc_path.name, doc_path.read_bytes()))
    if not chunks:
        raise SystemExit(f"No chunks produced from {docs_dir} — is it empty or missing supported files?")

    dataset = build_dataset(
        chunks,
        topic=args.topic,
        gemma=GemmaConceptExtractor(base_url=gemma_base_url),
        embedder=SentenceTransformerEmbedder(),
        fireworks_infer=PrerequisiteFireworksClient(api_key=fireworks_api_key),
        fireworks_teach=TeachFireworksClient(api_key=fireworks_api_key),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    print(f"Wrote {len(dataset['nodes'])} nodes / {len(dataset['edges'])} edges to {output_path}")


if __name__ == "__main__":
    main()
