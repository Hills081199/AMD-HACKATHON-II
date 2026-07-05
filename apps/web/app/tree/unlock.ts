import type { DisplayNode, NodeStatus, RawTreeNode, TreeEdge } from "./types";

/**
 * Derives each node's effective status from a single source of truth (the
 * completed-node set) plus the edge structure, rather than trusting a
 * possibly-stale `status` field from the data source. A node unlocks once
 * every edge pointing into it comes from a completed node; nodes with no
 * incoming edges (tier 0) unlock automatically. See
 * docs/concept-graph-pipeline.md's unlock mechanism description.
 */
export function deriveNodeStatuses(
  nodes: RawTreeNode[],
  edges: TreeEdge[],
  completedIds: ReadonlySet<string>
): Map<string, NodeStatus> {
  const prerequisitesById = new Map<string, string[]>();
  for (const node of nodes) {
    prerequisitesById.set(node.id, []);
  }
  for (const edge of edges) {
    prerequisitesById.get(edge.to)?.push(edge.from);
  }

  const statuses = new Map<string, NodeStatus>();
  for (const node of nodes) {
    if (completedIds.has(node.id)) {
      statuses.set(node.id, "completed");
      continue;
    }
    const prerequisites = prerequisitesById.get(node.id) ?? [];
    const unlocked = prerequisites.every((id) => completedIds.has(id));
    statuses.set(node.id, unlocked ? "unlocked" : "locked");
  }
  return statuses;
}

/** Seeds the completed-node set from the data source's own `status` field —
 * only "completed" is trusted as an initial fact; "locked"/"unlocked" are
 * always re-derived rather than copied, since they're implied by the graph
 * structure and would otherwise be able to drift out of sync with it. */
export function seedCompletedIds(nodes: RawTreeNode[]): Set<string> {
  return new Set(nodes.filter((node) => node.status === "completed").map((node) => node.id));
}

export function toDisplayNodes(
  nodes: RawTreeNode[],
  edges: TreeEdge[],
  completedIds: ReadonlySet<string>
): DisplayNode[] {
  const statuses = deriveNodeStatuses(nodes, edges, completedIds);
  return nodes.map((node) => ({
    id: node.id,
    label: node.title ?? node.name ?? node.id,
    level: node.level,
    status: statuses.get(node.id) ?? "locked",
  }));
}
