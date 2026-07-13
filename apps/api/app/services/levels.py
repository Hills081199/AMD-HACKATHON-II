"""Pipeline step 6 — assign tiers to a validated dependency graph.

See docs/concept-graph-pipeline.md step 6. Consumes feat-002's full concept
list plus feat-004's repaired edges (valid_dag) — the full concept list
matters because a graph built from edges alone would silently drop concepts
that have zero prerequisite relationships.
"""

from __future__ import annotations

import networkx as nx


def assign_levels(edges: list[dict], concepts: list[dict]) -> list[dict]:
    """Group concepts into tiers via nx.topological_generations() (not a
    plain topological_sort — a DAG genuinely admits multiple valid parallel
    branches, and tiers preserve that instead of flattening it into one
    line). Returns nodes[] with id/name/level/sources/status."""
    graph = nx.DiGraph()
    graph.add_nodes_from(concept["id"] for concept in concepts)
    for edge in edges:
        graph.add_edge(edge["from"], edge["to"])

    concepts_by_id = {concept["id"]: concept for concept in concepts}

    nodes: list[dict] = []
    for level, tier in enumerate(nx.topological_generations(graph)):
        for concept_id in tier:
            concept = concepts_by_id.get(concept_id, {})
            nodes.append(
                {
                    "id": concept_id,
                    "name": concept.get("name", concept_id),
                    "level": level,
                    # chunk_id already encodes "{doc_id}:p{page}" (see
                    # worker/ingest.py) — splitting it into separate doc_id/
                    # page fields to fully match docs/concept-graph-pipeline.md's
                    # source schema is deferred polish, not required here.
                    "sources": [{"chunk_id": chunk_id} for chunk_id in concept.get("chunk_ids", [])],
                    "status": "unlocked" if level == 0 else "locked",
                }
            )
    return nodes
