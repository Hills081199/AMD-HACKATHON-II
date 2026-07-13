"""Tests for pipeline step 6, tier assignment
(docs/concept-graph-pipeline.md step 6)."""

from app.services.levels import assign_levels


def test_assign_levels_preserves_parallel_branches_and_merges():
    # Mirrors docs/concept-graph-pipeline.md's sample tree shape: two
    # independent tier-0 roots, each feeding a tier-1 node, which converge
    # into a single tier-2 node.
    concepts = [
        {"id": "c1", "name": "Linear Algebra", "chunk_ids": ["d:p1"]},
        {"id": "c2", "name": "Calculus", "chunk_ids": ["d:p2"]},
        {"id": "c3", "name": "Data Vectorization", "chunk_ids": ["d:p3"]},
        {"id": "c4", "name": "Gradient Descent", "chunk_ids": ["d:p4"]},
        {"id": "c5", "name": "Linear Regression", "chunk_ids": ["d:p5"]},
    ]
    edges = [
        {"from": "c1", "to": "c3", "confidence": 0.9},
        {"from": "c3", "to": "c5", "confidence": 0.85},
        {"from": "c2", "to": "c4", "confidence": 0.9},
        {"from": "c4", "to": "c5", "confidence": 0.8},
    ]

    nodes = assign_levels(edges, concepts)
    level_by_id = {node["id"]: node["level"] for node in nodes}

    assert level_by_id["c1"] == 0
    assert level_by_id["c2"] == 0
    assert level_by_id["c3"] == 1
    assert level_by_id["c4"] == 1
    assert level_by_id["c5"] == 2  # two branches converge here

    # DAG tier invariant: every edge's child level must exceed its parent's.
    for edge in edges:
        assert level_by_id[edge["to"]] > level_by_id[edge["from"]]


def test_assign_levels_includes_isolated_concepts_as_tier_zero():
    concepts = [
        {"id": "c1", "name": "Linear Algebra", "chunk_ids": []},
        {"id": "c2", "name": "Unrelated Topic", "chunk_ids": []},  # no edges at all
    ]

    nodes = assign_levels(edges=[], concepts=concepts)

    assert {node["id"] for node in nodes} == {"c1", "c2"}
    assert all(node["level"] == 0 for node in nodes)
    assert all(node["status"] == "unlocked" for node in nodes)


def test_assign_levels_marks_non_zero_tiers_locked():
    concepts = [{"id": "c1", "name": "A", "chunk_ids": []}, {"id": "c2", "name": "B", "chunk_ids": []}]
    edges = [{"from": "c1", "to": "c2", "confidence": 0.9}]

    nodes = assign_levels(edges, concepts)
    by_id = {node["id"]: node for node in nodes}

    assert by_id["c1"]["status"] == "unlocked"
    assert by_id["c2"]["status"] == "locked"


def test_assign_levels_carries_chunk_ids_into_sources():
    concepts = [{"id": "c1", "name": "A", "chunk_ids": ["doc.pdf:p1", "doc.pdf:p2"]}]

    nodes = assign_levels(edges=[], concepts=concepts)

    assert nodes[0]["sources"] == [{"chunk_id": "doc.pdf:p1"}, {"chunk_id": "doc.pdf:p2"}]
