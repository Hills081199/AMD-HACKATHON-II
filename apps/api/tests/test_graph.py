"""Tests for pipeline step 5, the self-checking graph agent
(docs/concept-graph-pipeline.md step 5)."""

import networkx as nx

from app.services.graph import build_graph, repair_cycles, validate_graph


def test_build_graph_creates_digraph_with_confidence_attribute():
    edges = [{"from": "a", "to": "b", "confidence": 0.9}]
    graph = build_graph(edges)

    assert graph.has_edge("a", "b")
    assert graph.edges["a", "b"]["confidence"] == 0.9


def test_repair_cycles_leaves_an_acyclic_graph_unchanged():
    edges = [
        {"from": "a", "to": "b", "confidence": 0.9},
        {"from": "b", "to": "c", "confidence": 0.8},
    ]
    graph = build_graph(edges)

    valid_graph, dropped = repair_cycles(graph)

    assert dropped == []
    assert set(valid_graph.edges()) == {("a", "b"), ("b", "c")}


def test_repair_cycles_drops_the_lowest_confidence_edge_in_a_simple_cycle():
    # c -> a (0.3) is a mistaken, inverted prerequisite — the weakest edge
    # in the a -> b -> c -> a cycle, and the one that should be dropped.
    edges = [
        {"from": "a", "to": "b", "confidence": 0.9},
        {"from": "b", "to": "c", "confidence": 0.8},
        {"from": "c", "to": "a", "confidence": 0.3},
    ]
    graph = build_graph(edges)

    valid_graph, dropped = repair_cycles(graph, max_iterations=10)

    assert list(nx.simple_cycles(valid_graph)) == []
    assert dropped == [
        {
            "from": "c",
            "to": "a",
            "confidence": 0.3,
            "reason": "dropped lowest-confidence edge in a detected cycle (iteration 1)",
        }
    ]
    assert valid_graph.has_edge("a", "b")
    assert valid_graph.has_edge("b", "c")


def test_repair_cycles_force_drops_after_max_iterations_exhausted():
    # Two independent 2-cycles: repairing both needs 2 drops, but
    # max_iterations=1 only budgets 1 — the second must come from the
    # force-drop fallback, and the agent must still converge to a valid DAG.
    edges = [
        {"from": "a", "to": "b", "confidence": 0.9},
        {"from": "b", "to": "a", "confidence": 0.2},
        {"from": "c", "to": "d", "confidence": 0.85},
        {"from": "d", "to": "c", "confidence": 0.15},
    ]
    graph = build_graph(edges)

    valid_graph, dropped = repair_cycles(graph, max_iterations=1)

    assert list(nx.simple_cycles(valid_graph)) == []
    assert len(dropped) == 2
    assert dropped[0]["reason"].startswith("dropped lowest-confidence edge in a detected cycle")
    assert dropped[1]["reason"] == "force-dropped weakest edge — cycle survived max_iterations"
    assert {(d["from"], d["to"]) for d in dropped} == {("b", "a"), ("d", "c")}


def test_validate_graph_returns_valid_dag_and_dropped_log():
    edges = [
        {"from": "a", "to": "b", "confidence": 0.9},
        {"from": "b", "to": "a", "confidence": 0.1},
    ]

    result = validate_graph(edges)

    assert result["edges"] == [{"from": "a", "to": "b", "confidence": 0.9}]
    assert result["dropped_edges"] == [
        {
            "from": "b",
            "to": "a",
            "confidence": 0.1,
            "reason": "dropped lowest-confidence edge in a detected cycle (iteration 1)",
        }
    ]
