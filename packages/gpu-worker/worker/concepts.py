"""Pipeline steps 2-3 — concept extraction (Gemma) + clustering/dedupe.

See docs/concept-graph-pipeline.md steps 2-3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import networkx as nx
import numpy as np

from worker.ingest import Chunk


@dataclass
class RawConcept:
    name: str
    definition: str
    chunk_id: str


@dataclass
class CanonicalConcept:
    id: str
    name: str
    definition: str
    chunk_ids: list[str]
    embedding: list[float]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "chunk_ids": self.chunk_ids,
            "embedding": [float(x) for x in self.embedding],
        }


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

        prompt = (
            "List the distinct learning concepts this text teaches. Return "
            "strict JSON: a list of objects with 'name' (short canonical "
            "name) and 'definition' (one sentence). Text:\n\n" + chunk.text
        )
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "format": "json", "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        items = json.loads(response.json()["response"])
        return [
            RawConcept(name=item["name"], definition=item.get("definition", ""), chunk_id=chunk.chunk_id)
            for item in items
        ]


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


def extract_raw_concepts(chunks: list[Chunk], extractor: GemmaConceptExtractor) -> list[RawConcept]:
    raw: list[RawConcept] = []
    for chunk in chunks:
        raw.extend(extractor.extract(chunk))
    return raw


def cluster_concepts(
    raw_concepts: list[RawConcept], embed_fn, similarity_threshold: float = 0.9
) -> list[CanonicalConcept]:
    """Merge near-duplicate raw concepts into canonical nodes.

    No LLM call here by design (docs/concept-graph-pipeline.md step 3) —
    pure cosine similarity on embeddings + Louvain community detection.
    """
    if not raw_concepts:
        return []

    texts = [f"{concept.name}: {concept.definition}" for concept in raw_concepts]
    vectors = np.asarray(embed_fn(texts), dtype=float)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit_vectors = vectors / norms
    similarity = unit_vectors @ unit_vectors.T

    graph = nx.Graph()
    graph.add_nodes_from(range(len(raw_concepts)))
    for i in range(len(raw_concepts)):
        for j in range(i + 1, len(raw_concepts)):
            if similarity[i, j] >= similarity_threshold:
                graph.add_edge(i, j, weight=float(similarity[i, j]))

    communities = nx.algorithms.community.louvain_communities(graph, weight="weight", seed=0)

    canonical: list[CanonicalConcept] = []
    for community in communities:
        member_indices = sorted(community)
        members = [raw_concepts[i] for i in member_indices]
        # Shortest name wins as the canonical label — a simple, deterministic
        # heuristic that favors a concise phrasing (e.g. "gradient descent")
        # over a verbose restatement of the same idea.
        canonical_member = min(members, key=lambda concept: len(concept.name))
        # Centroid of the cluster's unit vectors — carried through so step 4
        # (prerequisite inference) can pre-filter candidate pairs by
        # similarity without re-embedding concepts from scratch.
        centroid = unit_vectors[member_indices].mean(axis=0)
        canonical.append(
            CanonicalConcept(
                id=f"concept_{len(canonical) + 1:03d}",
                name=canonical_member.name,
                definition=canonical_member.definition,
                chunk_ids=sorted({member.chunk_id for member in members}),
                embedding=centroid.tolist(),
            )
        )
    return canonical
