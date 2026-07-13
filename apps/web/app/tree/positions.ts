import type { DisplayNode } from "./types";

const LEVEL_SPACING_X = 220;
const NODE_SPACING_Y = 110;

/**
 * Places nodes in columns by level (tier 0 leftmost) — matching
 * docs/concept-graph-pipeline.md's "group them into columns/tiers by
 * level" description. Computed from `level` rather than trusting a
 * possible `position` field on the raw node, since the live API's
 * assign_levels() output (apps/api/app/services/levels.py) doesn't emit
 * one — only the static sample dataset does.
 */
export function layoutNodesByLevel(nodes: DisplayNode[]): Map<string, { x: number; y: number }> {
  const nodesByLevel = new Map<number, DisplayNode[]>();
  for (const node of nodes) {
    const bucket = nodesByLevel.get(node.level) ?? [];
    bucket.push(node);
    nodesByLevel.set(node.level, bucket);
  }

  const positions = new Map<string, { x: number; y: number }>();
  for (const [level, levelNodes] of nodesByLevel) {
    const sorted = [...levelNodes].sort((a, b) => a.id.localeCompare(b.id));
    sorted.forEach((node, index) => {
      positions.set(node.id, { x: level * LEVEL_SPACING_X, y: index * NODE_SPACING_Y });
    });
  }
  return positions;
}
