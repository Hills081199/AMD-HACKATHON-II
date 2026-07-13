import { useCallback, useMemo, useState } from "react";
import type { DisplayNode, TreeEdge } from "./types";

export interface EdgeId {
  from: string;
  to: string;
}

export interface PineInteractionState {
  hoveredId: string | null;
  selectedId: string | null;
  /** Nodes to show lit (not dimmed) */
  litNodeIds: Set<string>;
  /** Upstream (prerequisite) edge keys "from->to" */
  upstreamEdgeIds: Set<string>;
  /** Downstream (dependent) edge keys "from->to" */
  downstreamEdgeIds: Set<string>;
  /** Whether the scene is in a "focusing" mode (dim everything else) */
  isFocusing: boolean;
}

function edgeKey(from: string, to: string) {
  return `${from}->${to}`;
}

function buildAdjacency(edges: TreeEdge[]) {
  // prerequisites: node -> set of nodes it depends on (incoming edges)
  const prereqOf = new Map<string, string[]>();
  // dependents: node -> set of nodes that depend on it (outgoing edges)
  const dependentOf = new Map<string, string[]>();

  for (const edge of edges) {
    const from = edge.from ?? edge.source ?? "";
    const to = edge.to ?? edge.target ?? "";
    if (!prereqOf.has(to)) prereqOf.set(to, []);
    prereqOf.get(to)!.push(from);
    if (!dependentOf.has(from)) dependentOf.set(from, []);
    dependentOf.get(from)!.push(to);
  }
  return { prereqOf, dependentOf };
}

/** BFS walk upstream (prerequisites) or downstream (dependents) */
function walk(
  startId: string,
  adj: Map<string, string[]>
): Set<string> {
  const visited = new Set<string>();
  const queue = [startId];
  while (queue.length > 0) {
    const id = queue.shift()!;
    if (visited.has(id)) continue;
    visited.add(id);
    for (const neighbor of adj.get(id) ?? []) {
      queue.push(neighbor);
    }
  }
  return visited;
}

export function usePineInteraction(
  nodes: DisplayNode[],
  edges: TreeEdge[]
) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { prereqOf, dependentOf } = useMemo(
    () => buildAdjacency(edges),
    [edges]
  );

  // Immediate neighbors for hover
  const hoverState = useMemo<Omit<PineInteractionState, "hoveredId" | "selectedId" | "isFocusing">>(() => {
    if (!hoveredId) {
      return {
        litNodeIds: new Set(),
        upstreamEdgeIds: new Set(),
        downstreamEdgeIds: new Set(),
      };
    }
    const litNodeIds = new Set<string>([hoveredId]);
    const upstreamEdgeIds = new Set<string>();
    const downstreamEdgeIds = new Set<string>();

    for (const prereq of prereqOf.get(hoveredId) ?? []) {
      litNodeIds.add(prereq);
      upstreamEdgeIds.add(edgeKey(prereq, hoveredId));
    }
    for (const dep of dependentOf.get(hoveredId) ?? []) {
      litNodeIds.add(dep);
      downstreamEdgeIds.add(edgeKey(hoveredId, dep));
    }
    return { litNodeIds, upstreamEdgeIds, downstreamEdgeIds };
  }, [hoveredId, prereqOf, dependentOf]);

  // Full ancestor+descendant chain for click
  const selectState = useMemo<Omit<PineInteractionState, "hoveredId" | "selectedId" | "isFocusing">>(() => {
    if (!selectedId) {
      return {
        litNodeIds: new Set(),
        upstreamEdgeIds: new Set(),
        downstreamEdgeIds: new Set(),
      };
    }
    // Walk full upstream chain
    const ancestors = walk(selectedId, prereqOf);
    // Walk full downstream chain
    const descendants = walk(selectedId, dependentOf);

    const litNodeIds = new Set<string>([...ancestors, ...descendants]);

    const upstreamEdgeIds = new Set<string>();
    const downstreamEdgeIds = new Set<string>();

    for (const edge of edges) {
      const from = edge.from ?? edge.source ?? "";
      const to = edge.to ?? edge.target ?? "";
      if (ancestors.has(from) && ancestors.has(to)) {
        upstreamEdgeIds.add(edgeKey(from, to));
      }
      if (descendants.has(from) && descendants.has(to)) {
        downstreamEdgeIds.add(edgeKey(from, to));
      }
    }
    return { litNodeIds, upstreamEdgeIds, downstreamEdgeIds };
  }, [selectedId, prereqOf, dependentOf, edges]);

  // Merge: click wins over hover
  const activeState = selectedId ? selectState : hoverState;
  const isFocusing = selectedId !== null || hoveredId !== null;

  const onHoverNode = useCallback((id: string | null) => {
    setHoveredId(id);
  }, []);

  const onClickNode = useCallback((id: string) => {
    setSelectedId((prev) => (prev === id ? null : id));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedId(null);
    setHoveredId(null);
  }, []);

  return {
    hoveredId,
    selectedId,
    isFocusing,
    ...activeState,
    onHoverNode,
    onClickNode,
    clearSelection,
  };
}
