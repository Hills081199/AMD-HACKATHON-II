"""Tests for scripts/build_demo_dataset.py's orchestration logic (feat-009).

These verify that build_dataset() correctly wires together the already-unit-
tested feat-001..feat-007 functions and assembles the final schema — they
inject fakes for Gemma/embedding/Fireworks (no live credentials needed, same
pattern as every other feature's tests), but run real chunk_document() over
the real, checked-in documents in data/source_docs/, so the input side of
this test is genuine pipeline data, not a synthetic fixture.

This does NOT verify feat-009 end to end — that requires a live
GEMMA_BASE_URL and FIREWORKS_API_KEY, which this environment doesn't have
(see feature_list.json's feat-009 entry and progress.md for the documented
blocker). It verifies that the orchestration code itself is correct, so
running it for real (once credentials exist) is just a matter of supplying
them — see scripts/build_demo_dataset.py's own docstring for the command.
"""

import sys
from pathlib import Path

import networkx as nx

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "packages" / "gpu-worker"))
sys.path.insert(0, str(_REPO_ROOT / "apps" / "api"))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from worker.ingest import chunk_document  # noqa: E402

from build_demo_dataset import build_dataset  # noqa: E402

_SOURCE_DOCS_DIR = _REPO_ROOT / "data" / "source_docs"


class _FakeGemma:
    """Tags each chunk with one concept derived from its own first line (the
    heading/title every generated source doc starts with), so the fake
    output stays traceable to real chunk text instead of being arbitrary."""

    def extract(self, chunk):
        from worker.concepts import RawConcept

        heading = chunk.text.splitlines()[0]
        return [RawConcept(name=heading, definition=f"About {heading}.", chunk_id=chunk.chunk_id)]


def _fake_embed(texts: list[str]):
    """Deterministic, dependency-free stand-in for a real sentence-transformer.
    Every vector has a shared baseline component (so distinct concepts still
    have some similarity — 0.5 cosine between any two — letting
    pre_filter_pairs find candidate pairs the way real embeddings of a
    single-domain corpus would) plus a unique one-hot component (so
    cluster_concepts() never accidentally merges two different concepts,
    since 0.5 stays below its 0.9 dedup threshold)."""
    import numpy as np

    unique_texts = sorted(set(texts))
    index_by_text = {text: index for index, text in enumerate(unique_texts)}
    dimension = len(unique_texts) + 1
    vectors = np.zeros((len(texts), dimension))
    for row, text in enumerate(texts):
        vectors[row, 0] = 1.0
        vectors[row, 1 + index_by_text[text]] = 1.0
    return vectors


class _FakePrerequisiteFireworks:
    """Chains concepts in the order they were pre-filtered — deterministic,
    not meaningful reasoning, since real prerequisite inference requires a
    live Fireworks call (the thing this test is explicitly not covering)."""

    def infer_direction(self, concept_a, concept_b):
        return {"direction": "a_before_b", "confidence": 0.9}


class _FakeTeachFireworks:
    def generate(self, node_name, chunks):
        return {
            "lesson": f"A short lesson about {node_name}.",
            "quiz": {"question": f"What is {node_name}?", "options": ["a", "b"], "answer_index": 0},
            "example": f"A real-world example of {node_name}.",
        }

    def check_alignment(self, node_name, lesson, quiz):
        return True


def _load_real_chunks():
    chunks = []
    for doc_path in sorted(_SOURCE_DOCS_DIR.iterdir()):
        chunks.extend(chunk_document(doc_path.name, doc_path.read_bytes()))
    return chunks


def test_source_docs_directory_has_real_documents():
    # Guards against this test silently passing on an empty/missing dir.
    assert _SOURCE_DOCS_DIR.exists()
    doc_files = list(_SOURCE_DOCS_DIR.iterdir())
    assert len(doc_files) >= 5


def test_build_dataset_produces_a_schema_matching_valid_dag_and_tiers():
    chunks = _load_real_chunks()
    assert len(chunks) > 0

    dataset = build_dataset(
        chunks,
        topic="Introduction to Machine Learning",
        gemma=_FakeGemma(),
        embedder=_fake_embed,
        fireworks_infer=_FakePrerequisiteFireworks(),
        fireworks_teach=_FakeTeachFireworks(),
    )

    assert dataset["topic"] == "Introduction to Machine Learning"
    assert len(dataset["nodes"]) > 0
    assert len(dataset["edges"]) > 0

    # DAG tier invariant, same check the live /trees/{topic_id} endpoint test
    # runs against the hand-written sample (apps/api/tests/test_trees_endpoint.py).
    level_by_id = {node["id"]: node["level"] for node in dataset["nodes"]}
    for edge in dataset["edges"]:
        assert level_by_id[edge["to"]] > level_by_id[edge["from"]]

    graph = nx.DiGraph()
    graph.add_nodes_from(level_by_id)
    graph.add_edges_from((edge["from"], edge["to"]) for edge in dataset["edges"])
    assert list(nx.simple_cycles(graph)) == []


def test_build_dataset_every_node_has_a_lesson_quiz_and_own_sources_only():
    chunks = _load_real_chunks()
    all_chunk_ids = {chunk.chunk_id for chunk in chunks}

    dataset = build_dataset(
        chunks,
        topic="Introduction to Machine Learning",
        gemma=_FakeGemma(),
        embedder=_fake_embed,
        fireworks_infer=_FakePrerequisiteFireworks(),
        fireworks_teach=_FakeTeachFireworks(),
    )

    for node in dataset["nodes"]:
        assert node["lesson"]["summary"]
        assert node["quiz"]["questions"], f"node {node['id']} has no quiz question"
        assert node["sources"], f"node {node['id']} has no sources"
        # Every cited source must trace back to a real ingested chunk's
        # doc_id — nothing fabricated, nothing from outside this run's docs.
        cited_doc_ids = {source["doc_id"] for source in node["sources"]}
        real_doc_ids = {chunk.doc_id for chunk in chunks if chunk.chunk_id in all_chunk_ids}
        assert cited_doc_ids <= real_doc_ids
