import type { DisplayNode, TreeEdge } from "./types";

/** Maximum nodes to render by default without clustering. */
export const CLUSTER_THRESHOLD = 60;
/** Default cap for the rendered subset when clustering is active. */
export const DEFAULT_MAX_NODES = 48;

export interface ClusterResult {
  displayNodes: DisplayNode[];
  displayEdges: TreeEdge[];
  isFiltered: boolean;
  totalNodeCount: number;
  totalEdgeCount: number;
}

/**
 * For graphs larger than CLUSTER_THRESHOLD, picks a representative subset:
 * 1. All completed/unlocked nodes (player progress always visible)
 * 2. Highest-degree nodes per tier (most connected = most structurally important)
 * 3. Fill remaining slots with remaining nodes sorted by degree descending
 */
export function clusterForDisplay(
  allNodes: DisplayNode[],
  allEdges: TreeEdge[],
  maxNodes: number = DEFAULT_MAX_NODES
): ClusterResult {
  const totalNodeCount = allNodes.length;
  const totalEdgeCount = allEdges.length;

  if (totalNodeCount <= CLUSTER_THRESHOLD) {
    return {
      displayNodes: allNodes,
      displayEdges: allEdges,
      isFiltered: false,
      totalNodeCount,
      totalEdgeCount,
    };
  }

  // Build degree map
  const degree = new Map<string, number>();
  for (const node of allNodes) degree.set(node.id, 0);
  for (const edge of allEdges) {
    const from = edge.from ?? edge.source ?? "";
    const to = edge.to ?? edge.target ?? "";
    degree.set(from, (degree.get(from) ?? 0) + 1);
    degree.set(to, (degree.get(to) ?? 0) + 1);
  }

  const selected = new Set<string>();

  // Priority 1: all completed/unlocked nodes
  for (const node of allNodes) {
    if (node.status !== "locked") selected.add(node.id);
  }

  // Priority 2: highest-degree per tier
  const byLevel = new Map<number, DisplayNode[]>();
  for (const node of allNodes) {
    if (!byLevel.has(node.level)) byLevel.set(node.level, []);
    byLevel.get(node.level)!.push(node);
  }

  const numTiers = byLevel.size;
  const slotsPerTier = Math.max(1, Math.floor((maxNodes - selected.size) / numTiers));

  for (const [, tierNodes] of byLevel) {
    const sorted = [...tierNodes].sort(
      (a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0)
    );
    for (let i = 0; i < slotsPerTier && selected.size < maxNodes; i++) {
      if (sorted[i]) selected.add(sorted[i].id);
    }
  }

  // Priority 3: fill remaining slots by degree
  if (selected.size < maxNodes) {
    const remaining = allNodes
      .filter((n) => !selected.has(n.id))
      .sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0));
    for (const node of remaining) {
      if (selected.size >= maxNodes) break;
      selected.add(node.id);
    }
  }

  const displayNodes = allNodes.filter((n) => selected.has(n.id));
  const displayEdges = allEdges.filter((e) => {
    const from = e.from ?? e.source ?? "";
    const to = e.to ?? e.target ?? "";
    return selected.has(from) && selected.has(to);
  });

  return {
    displayNodes,
    displayEdges,
    isFiltered: true,
    totalNodeCount,
    totalEdgeCount,
  };
}
