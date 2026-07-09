"""Pipeline step 5 — self-checking graph agent (cycle/redundancy repair).

See docs/concept-graph-pipeline.md step 5. Consumes packages/gpu-worker's
POST /build-graph output (candidate_edges[]) — see docs/architecture.md's
Data contract section: gpu-worker produces the candidate graph, api starts
here with validation.
"""

from __future__ import annotations

import networkx as nx


def build_graph(edges: list[dict]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for edge in edges:
        graph.add_edge(edge["from"], edge["to"], confidence=edge["confidence"])
    return graph


def _weakest_edge_in_cycle(graph: nx.DiGraph, cycle: list) -> tuple[str, str]:
    edges_in_cycle = [(cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle))]
    return min(edges_in_cycle, key=lambda edge: graph.edges[edge]["confidence"])


def repair_cycles(graph: nx.DiGraph, max_iterations: int = 10) -> tuple[nx.DiGraph, list[dict]]:
    """Repeatedly drop the lowest-confidence edge in a detected cycle until
    none remain, bounded by max_iterations. If a cycle survives that budget,
    fall back to force-dropping the weakest edge regardless, so the agent
    always terminates with a valid DAG."""
    graph = graph.copy()
    dropped: list[dict] = []

    for iteration in range(1, max_iterations + 1):
        cycles = list(nx.simple_cycles(graph))
        if not cycles:
            return graph, dropped
        cycle = min(cycles, key=len)
        u, v = _weakest_edge_in_cycle(graph, cycle)
        confidence = graph.edges[u, v]["confidence"]
        graph.remove_edge(u, v)
        dropped.append(
            {
                "from": u,
                "to": v,
                "confidence": confidence,
                "reason": f"dropped lowest-confidence edge in a detected cycle (iteration {iteration})",
            }
        )

    while True:
        cycles = list(nx.simple_cycles(graph))
        if not cycles:
            break
        cycle = min(cycles, key=len)
        u, v = _weakest_edge_in_cycle(graph, cycle)
        confidence = graph.edges[u, v]["confidence"]
        graph.remove_edge(u, v)
        dropped.append(
            {
                "from": u,
                "to": v,
                "confidence": confidence,
                "reason": "force-dropped weakest edge — cycle survived max_iterations",
            }
        )

    return graph, dropped


def validate_graph(edges: list[dict], max_iterations: int = 10) -> dict:
    """Build a DiGraph from candidate_edges[] and repair any cycles.
    Then applies transitive reduction to remove redundant edges for a cleaner UI.

    Returns {"edges": valid_dag's edges, "dropped_edges": the repair log} —
    the log is what makes this an auditable "self-checking agent" rather
    than a silent filter (see docs/hackathon-scope.md §3).
    """
    graph = build_graph(edges)
    valid_graph, dropped_edges = repair_cycles(graph, max_iterations=max_iterations)
    
    # Perform transitive reduction to clean up redundant paths 
    # (e.g. if A->B and B->C, remove A->C)
    reduced_graph = nx.transitive_reduction(valid_graph)
    
    return {
        "edges": [
            {"from": u, "to": v, "confidence": valid_graph.edges[u, v]["confidence"]}
            for u, v in reduced_graph.edges()
        ],
        "dropped_edges": dropped_edges,
    }
