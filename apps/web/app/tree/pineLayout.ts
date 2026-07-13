import type { DisplayNode } from "./types";

export const LEVEL_SPACING_Y = 80; // tighter vertical spacing for compact tree
export const TOP_PADDING = 60;
export const BOTTOM_PADDING = 180; // space for trunk + root label
export const CANVAS_WIDTH = 1200;
export const MIN_CANVAS_HEIGHT = 700;

export interface PinePosition {
  x: number;
  y: number;
}

export interface PineLayout {
  positions: Map<string, PinePosition>;
  canvasWidth: number;
  canvasHeight: number;
  numTiers: number;
  maxLevel: number;
}

/**
 * Bottom-up pine-tree layout:
 * - Level 0 (roots/foundational) sits at the BOTTOM of the canvas.
 * - Each higher level moves UPWARD toward the treetop.
 * - Nodes within a tier spread horizontally, narrowing as levels increase
 *   (pine silhouette: wide base, narrow apex).
 */
export function computePineLayout(nodes: DisplayNode[]): PineLayout {
  if (nodes.length === 0) {
    return {
      positions: new Map(),
      canvasWidth: CANVAS_WIDTH,
      canvasHeight: MIN_CANVAS_HEIGHT,
      numTiers: 0,
      maxLevel: 0,
    };
  }

  // Group nodes by level
  const byLevel = new Map<number, DisplayNode[]>();
  for (const node of nodes) {
    if (!byLevel.has(node.level)) byLevel.set(node.level, []);
    byLevel.get(node.level)!.push(node);
  }

  const levels = [...byLevel.keys()].sort((a, b) => a - b);
  const maxLevel = levels[levels.length - 1] ?? 0;
  const numTiers = levels.length;

  const canvasHeight = Math.max(
    MIN_CANVAS_HEIGHT,
    numTiers * LEVEL_SPACING_Y + TOP_PADDING + BOTTOM_PADDING
  );

  const positions = new Map<string, PinePosition>();
  const centerX = CANVAS_WIDTH / 2;

  for (const level of levels) {
    const tierNodes = byLevel.get(level) ?? [];
    const sorted = [...tierNodes].sort((a, b) => a.id.localeCompare(b.id));

    // Y: level 0 is at the bottom, higher levels move upward
    const y = canvasHeight - BOTTOM_PADDING - level * LEVEL_SPACING_Y;

    // X spread: wide at bottom, narrows toward top (pine shape)
    // Use exponential curve for more natural pine tree silhouette
    const tRatio = maxLevel > 0 ? level / maxLevel : 0;
    // Exponential narrowing: starts wide, narrows more aggressively toward top
    const narrowFactor = Math.pow(1 - tRatio, 0.6); // 0.6 exponent for gentle curve
    const minSpread = 80; // minimum spread at top
    const maxSpread = CANVAS_WIDTH * 0.85; // ~1020px at base
    const spreadWidth = minSpread + (maxSpread - minSpread) * narrowFactor;
    const n = sorted.length;

    sorted.forEach((node, idx) => {
      let x: number;
      if (n === 1) {
        x = centerX;
      } else {
        const step = spreadWidth / (n - 1);
        x = centerX - spreadWidth / 2 + idx * step;
      }
      positions.set(node.id, { x: Math.round(x), y: Math.round(y) });
    });
  }

  return { positions, canvasWidth: CANVAS_WIDTH, canvasHeight, numTiers, maxLevel };
}
