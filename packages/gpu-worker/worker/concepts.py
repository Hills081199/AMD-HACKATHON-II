"""Pipeline steps 2-3 — concept extraction (Gemma) + clustering/dedupe.

See docs/concept-graph-pipeline.md steps 2-3.

IMP-A1: RawConcept and CanonicalConcept now carry a `difficulty` field
('foundational' | 'intermediate' | 'advanced'). Both extractors ask the LLM
to estimate difficulty; the field flows through clustering and is preserved in
CanonicalConcept.to_dict() so Step 4 can use it to improve direction inference.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import networkx as nx
import numpy as np

from worker.ingest import Chunk

# Valid difficulty levels produced by the extraction prompt
_VALID_DIFFICULTIES = {"foundational", "intermediate", "advanced"}
_DEFAULT_DIFFICULTY = "intermediate"


@dataclass
class RawConcept:
    name: str
    definition: str
    chunk_id: str
    difficulty: str = field(default=_DEFAULT_DIFFICULTY)  # IMP-A1


@dataclass
class CanonicalConcept:
    id: str
    name: str
    definition: str
    chunk_ids: list[str]
    embedding: list[float]
    difficulty: str = field(default=_DEFAULT_DIFFICULTY)  # IMP-A1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "difficulty": self.difficulty,
            "chunk_ids": self.chunk_ids,
            "embedding": [float(x) for x in self.embedding],
        }


def _coerce_difficulty(value: str | None) -> str:
    """Normalise whatever the LLM returned to a canonical difficulty level."""
    if not value:
        return _DEFAULT_DIFFICULTY
    v = value.strip().lower()
    if v in _VALID_DIFFICULTIES:
        return v
    # Fuzzy match
    for level in ("foundational", "intermediate", "advanced"):
        if level in v:
            return level
    return _DEFAULT_DIFFICULTY


class GemmaConceptExtractor:
    """Client for Gemma served locally via vLLM-ROCm or Ollama, on the AMD GPU.

    Deliberately not a hosted API call: local inference is what qualifies for
    the Best Use of Gemma bonus and the AMD-platform-usage judging criterion
    (see docs/brd.md §4.3, §7.3).
    """

    def __init__(self, base_url: str, model: str = "gemma2:9b", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def extract(self, chunk: Chunk) -> list[RawConcept]:
        import httpx

        # IMP-A1: ask for difficulty level per concept
        prompt = (
            "List the distinct learning concepts this text teaches. "
            "For each concept, also estimate its difficulty: "
            "'foundational' (can be understood without other concepts), "
            "'intermediate' (requires some background knowledge), or "
            "'advanced' (requires multiple prerequisites to understand). "
            "Return strict JSON: {\"concepts\": [{\"name\": <short canonical name>, "
            "\"definition\": <one sentence>, "
            "\"difficulty\": \"foundational\"|\"intermediate\"|\"advanced\"}, ...]}.\n\n"
            "Text:\n\n" + chunk.text
        )
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "format": "json", "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        items = json.loads(response.json()["response"]).get("concepts", [])
        return [
            RawConcept(
                name=item["name"],
                definition=item.get("definition", ""),
                chunk_id=chunk.chunk_id,
                difficulty=_coerce_difficulty(item.get("difficulty")),
            )
            for item in items
        ]

    def extract_batch(self, chunks: list[Chunk]) -> list[RawConcept]:
        """Extract concepts from several chunks in a single LLM call.

        Cuts the request count (and repeated instruction tokens) vs. one
        call per chunk. Each text is tagged with its index so returned
        concepts map back to the right chunk_id; a batch of one degrades to
        the same result as extract().
        """
        if not chunks:
            return []

        import httpx

        blocks = "\n\n".join(f"[CHUNK {i}]\n{chunk.text}" for i, chunk in enumerate(chunks))
        # IMP-A1: batch prompt also requests difficulty
        prompt = (
            "You are given several text chunks, each marked '[CHUNK i]'. For "
            "each chunk, list the distinct learning concepts it teaches. "
            "For each concept estimate its difficulty: 'foundational', "
            "'intermediate', or 'advanced'. "
            "Return strict JSON: {\"results\": [{\"chunk_index\": <int>, "
            "\"concepts\": [{\"name\": <short canonical name>, \"definition\": "
            "<one sentence>, \"difficulty\": \"foundational\"|\"intermediate\"|\"advanced\"}, ...]}, ...]}\n\n"
            + blocks
        )
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "format": "json", "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        results = json.loads(response.json()["response"]).get("results", [])
        return _raw_concepts_from_batch(results, chunks)


class OpenAIConceptExtractor:
    """Prototyping-only stand-in for GemmaConceptExtractor, used to validate
    the end-to-end pipeline against a hosted model (GPT-4o mini) before
    real ROCm/Gemma infrastructure is available — see
    docs/hackathon-scope.md §5's Day-1 risk note. Selected via
    LLM_PROVIDER=openai in worker/main.py's get_gemma_extractor(); do not use
    this for the actual submission (see GemmaConceptExtractor's docstring
    for why local Gemma inference is required for judging, not just this
    step's own correctness)."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None, timeout: float = 30.0):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
        self.timeout = timeout

    def extract(self, chunk: Chunk) -> list[RawConcept]:
        import httpx

        # IMP-A1: prompt requests difficulty level
        prompt = (
            "List the distinct learning concepts this text teaches. "
            "For each concept, estimate its difficulty: "
            "'foundational' (no prerequisites needed), "
            "'intermediate' (requires some background), or "
            "'advanced' (requires multiple prerequisites). "
            "Respond with strict JSON only: {\"concepts\": [{\"name\": <short "
            "canonical name>, \"definition\": <one sentence>, "
            "\"difficulty\": \"foundational\"|\"intermediate\"|\"advanced\"}, ...]}.\n\n"
            "Text:\n\n" + chunk.text
        )
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        items = json.loads(content).get("concepts", [])
        return [
            RawConcept(
                name=item["name"],
                definition=item.get("definition", ""),
                chunk_id=chunk.chunk_id,
                difficulty=_coerce_difficulty(item.get("difficulty")),
            )
            for item in items
        ]

    def extract_batch(self, chunks: list[Chunk]) -> list[RawConcept]:
        """Batched counterpart to extract() — see GemmaConceptExtractor.extract_batch."""
        if not chunks:
            return []

        import httpx

        blocks = "\n\n".join(f"[CHUNK {i}]\n{chunk.text}" for i, chunk in enumerate(chunks))
        # IMP-A1: batch prompt requests difficulty
        prompt = (
            "You are given several text chunks, each marked '[CHUNK i]'. For "
            "each chunk, list the distinct learning concepts it teaches. "
            "For each concept, estimate difficulty: 'foundational', 'intermediate', or 'advanced'. "
            "Respond with strict JSON only: {\"results\": [{\"chunk_index\": "
            "<int>, \"concepts\": [{\"name\": <short canonical name>, "
            "\"definition\": <one sentence>, "
            "\"difficulty\": \"foundational\"|\"intermediate\"|\"advanced\"}, ...]}, ...]}\n\n"
            + blocks
        )
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        results = json.loads(content).get("results", [])
        return _raw_concepts_from_batch(results, chunks)


class OpenAIEmbedder:
    """Prototyping-only stand-in for SentenceTransformerEmbedder — avoids a
    ~1.3GB bge-large model download when validating the pipeline against a
    hosted API. Selected via LLM_PROVIDER=openai in worker/main.py's
    get_embedder()."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None, timeout: float = 30.0):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.environ.get("OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small"
        self.timeout = timeout

    def __call__(self, texts: list[str]) -> np.ndarray:
        import httpx

        response = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        return np.asarray([item["embedding"] for item in data])


class FireworksConceptExtractor:
    """Concept extractor backed by Fireworks AI's OpenAI-compatible chat
    completions API. Selected via LLM_PROVIDER=fireworks (the default
    hosted path). Uses the same prompt shape as OpenAIConceptExtractor;
    the two are wire-compatible because Fireworks mirrors the OpenAI API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ):
        self.api_key = api_key or os.environ.get("FIREWORKS_API_KEY", "")
        self.base_url = (
            base_url or os.environ.get("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
        ).rstrip("/")
        self.model = model or os.environ.get(
            "FIREWORKS_MODEL", "accounts/fireworks/models/deepseek-v4-pro"
        )
        self.timeout = timeout

    def extract(self, chunk: Chunk) -> list[RawConcept]:
        import httpx

        prompt = (
            "List the distinct learning concepts this text teaches. "
            "For each concept, estimate its difficulty: "
            "'foundational' (no prerequisites needed), "
            "'intermediate' (requires some background), or "
            "'advanced' (requires multiple prerequisites). "
            "Respond with strict JSON only — no prose, no markdown, no code fences: "
            '{"concepts": [{"name": <short canonical name>, "definition": <one sentence>, '
            '"difficulty": "foundational"|"intermediate"|"advanced"}, ...]}.\n\n'
            "Text:\n\n" + chunk.text
        )
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        # Strip markdown fences the model may emit despite the prompt instruction
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        items = json.loads(content).get("concepts", [])
        return [
            RawConcept(
                name=item["name"],
                definition=item.get("definition", ""),
                chunk_id=chunk.chunk_id,
                difficulty=_coerce_difficulty(item.get("difficulty")),
            )
            for item in items
        ]

    def extract_batch(self, chunks: list[Chunk]) -> list[RawConcept]:
        """Batched counterpart to extract() — see GemmaConceptExtractor.extract_batch."""
        if not chunks:
            return []

        import httpx

        blocks = "\n\n".join(f"[CHUNK {i}]\n{chunk.text}" for i, chunk in enumerate(chunks))
        prompt = (
            "You are given several text chunks, each marked '[CHUNK i]'. For "
            "each chunk, list the distinct learning concepts it teaches. "
            "For each concept, estimate difficulty: 'foundational', 'intermediate', or 'advanced'. "
            "Respond with strict JSON only — no prose, no markdown, no code fences: "
            '{"results": [{"chunk_index": <int>, "concepts": [{"name": <short canonical name>, '
            '"definition": <one sentence>, '
            '"difficulty": "foundational"|"intermediate"|"advanced"}, ...]}, ...]}\n\n'
            + blocks
        )
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        results = json.loads(content).get("results", [])
        return _raw_concepts_from_batch(results, chunks)


class FireworksEmbedder:
    """Embedder backed by Fireworks AI's OpenAI-compatible embeddings endpoint.
    Selected via LLM_PROVIDER=fireworks (the default hosted path). Avoids the
    ~1.3GB local model download when running without ROCm hardware."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("FIREWORKS_API_KEY", "")
        self.base_url = (
            base_url or os.environ.get("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
        ).rstrip("/")
        self.model = model or os.environ.get(
            "FIREWORKS_EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v1.5"
        )
        self.timeout = timeout

    def __call__(self, texts: list[str]) -> np.ndarray:
        import httpx

        response = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        return np.asarray([item["embedding"] for item in data])


class SentenceTransformerEmbedder:
    """Wraps sentence-transformers (bge-large/e5-large) on ROCm-enabled torch.

    Lazily loads the model on first call so importing this module — or
    running the test suite with a fake embedder injected instead — never
    requires torch, ROCm, or a model download.
    """

    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        self._model_name = model_name
        self._model = None

    def __call__(self, texts: list[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return np.asarray(self._model.encode(texts))


def _raw_concepts_from_batch(results: list[dict], chunks: list[Chunk]) -> list[RawConcept]:
    """Map a batched LLM response back to RawConcepts by chunk index.

    Results whose chunk_index is missing or out of range are skipped rather
    than raising, so one malformed entry doesn't lose the whole batch.
    """
    raw: list[RawConcept] = []
    for result in results:
        index = result.get("chunk_index")
        if not isinstance(index, int) or not (0 <= index < len(chunks)):
            continue
        chunk_id = chunks[index].chunk_id
        for item in result.get("concepts", []):
            raw.append(
                RawConcept(
                    name=item["name"],
                    definition=item.get("definition", ""),
                    chunk_id=chunk_id,
                    difficulty=_coerce_difficulty(item.get("difficulty")),  # IMP-A1
                )
            )
    return raw


def extract_raw_concepts(
    chunks: list[Chunk],
    extractor,
    batch_size: int | None = None,
    max_workers: int | None = None,
) -> list[RawConcept]:
    """Extract raw concepts from all chunks, batched and run in parallel.

    Chunks are grouped into batches of `batch_size` (one LLM call each), and
    the batches run concurrently across `max_workers` threads. This cuts both
    the call count (batching) and wall-clock time (parallelism) vs. the old
    one-sequential-call-per-chunk approach, with no change to the extraction
    prompt itself. Defaults come from CONCEPT_BATCH_SIZE / CONCEPT_MAX_WORKERS
    (5 and 4). Extractors without extract_batch fall back to per-chunk extract().
    """
    if not chunks:
        return []

    if batch_size is None:
        batch_size = int(os.environ.get("CONCEPT_BATCH_SIZE", "5"))
    if max_workers is None:
        max_workers = int(os.environ.get("CONCEPT_MAX_WORKERS", "4"))
    batch_size = max(1, batch_size)
    max_workers = max(1, max_workers)

    batches = [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]
    if hasattr(extractor, "extract_batch"):
        run = extractor.extract_batch
    else:
        def run(batch: list[Chunk]) -> list[RawConcept]:
            out: list[RawConcept] = []
            for chunk in batch:
                out.extend(extractor.extract(chunk))
            return out

    if max_workers == 1 or len(batches) == 1:
        batch_results = [run(batch) for batch in batches]
    else:
        with ThreadPoolExecutor(max_workers=min(max_workers, len(batches))) as executor:
            batch_results = list(executor.map(run, batches))

    raw: list[RawConcept] = []
    for result in batch_results:
        raw.extend(result)
    return raw


def _compute_adaptive_threshold(
    similarity: np.ndarray,
    target_percentile: float = 95.0
) -> float:
    """
    Computes the threshold as the `target_percentile`-th percentile of
    all off-diagonal similarity values. This makes the threshold adaptive
    to the embedding model's actual output distribution.
    """
    n = similarity.shape[0]
    if n < 2:
        return 0.9
    upper_tri = similarity[np.triu_indices(n, k=1)]
    if upper_tri.size == 0:
        return 0.9
    return float(np.percentile(upper_tri, target_percentile))


# IMP-A1: difficulty ordering for canonical selection tie-breaking
_DIFFICULTY_ORDER = {"foundational": 0, "intermediate": 1, "advanced": 2}


def cluster_concepts(
    raw_concepts: list[RawConcept],
    embed_fn,
    similarity_threshold: float | None = None,
    dedup_percentile: float = 95.0,
) -> list[CanonicalConcept]:
    """Merge near-duplicate raw concepts into canonical nodes.

    No LLM call here by design (docs/concept-graph-pipeline.md step 3) —
    pure cosine similarity on embeddings + Louvain community detection.

    IMP-A1: canonical difficulty is derived by majority vote within each cluster.
    """
    if not raw_concepts:
        return []

    texts = [f"{concept.name}: {concept.definition}" for concept in raw_concepts]
    vectors = np.asarray(embed_fn(texts), dtype=float)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit_vectors = vectors / norms
    similarity = unit_vectors @ unit_vectors.T

    if similarity_threshold is None:
        similarity_threshold = _compute_adaptive_threshold(similarity, dedup_percentile)

    graph = nx.Graph()
    graph.add_nodes_from(range(len(raw_concepts)))
    for i in range(len(raw_concepts)):
        for j in range(i + 1, len(raw_concepts)):
            if similarity[i, j] >= similarity_threshold:
                graph.add_edge(i, j, weight=float(similarity[i, j]))

    total_weight = sum(d.get("weight", 1.0) for _, _, d in graph.edges(data=True))
    if total_weight == 0 or graph.number_of_edges() == 0:
        # No meaningful similarity edges — every concept is its own singleton.
        # Louvain raises ZeroDivisionError on a graph with zero total edge weight.
        communities = [{i} for i in range(len(raw_concepts))]
    else:
        communities = nx.algorithms.community.louvain_communities(graph, weight="weight", seed=0)

    canonical: list[CanonicalConcept] = []
    for community in communities:
        member_indices = sorted(community)
        members = [raw_concepts[i] for i in member_indices]

        def quality_score(concept: RawConcept) -> tuple:
            name = concept.name
            is_acronym = name.isupper() and len(name) <= 5
            return (
                not is_acronym,
                len(concept.definition),
                -len(name),
            )

        canonical_member = max(members, key=quality_score)

        # IMP-A1: cluster difficulty = most common difficulty among members
        # (majority vote; ties broken toward foundational = safest for ordering)
        difficulty_counts: dict[str, int] = {}
        for m in members:
            difficulty_counts[m.difficulty] = difficulty_counts.get(m.difficulty, 0) + 1
        cluster_difficulty = min(
            difficulty_counts,
            key=lambda d: (-difficulty_counts[d], _DIFFICULTY_ORDER.get(d, 1)),
        )

        # Centroid of the cluster's unit vectors — carried through so step 4
        # (prerequisite inference) can pre-filter candidate pairs by
        # similarity without re-embedding concepts from scratch.
        centroid = unit_vectors[member_indices].mean(axis=0)
        centroid_norm = np.linalg.norm(centroid)
        if centroid_norm > 0:
            centroid = centroid / centroid_norm

        canonical.append(
            CanonicalConcept(
                id=f"concept_{len(canonical) + 1:03d}",
                name=canonical_member.name,
                definition=canonical_member.definition,
                difficulty=cluster_difficulty,
                chunk_ids=sorted({member.chunk_id for member in members}),
                embedding=centroid.tolist(),
            )
        )
    return canonical
