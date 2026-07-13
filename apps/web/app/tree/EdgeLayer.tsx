"use client";

import type { TreeEdge } from "./types";
import type { PineLayout } from "./pineLayout";

interface EdgeLayerProps {
  edges: TreeEdge[];
  layout: PineLayout;
  isFocusing: boolean;
  upstreamEdgeIds: Set<string>;
  downstreamEdgeIds: Set<string>;
}

function edgeKey(from: string, to: string) {
  return `${from}->${to}`;
}

/**
 * SVG layer that draws quadratic bezier edges between nodes.
 * When isFocusing=true, unlit edges fade to near-invisible.
 * Lit edges animate with a flowing dash in cyan (upstream) or emerald (downstream).
 */
export function EdgeLayer({
  edges,
  layout,
  isFocusing,
  upstreamEdgeIds,
  downstreamEdgeIds,
}: EdgeLayerProps) {
  const { positions, canvasWidth, canvasHeight } = layout;

  return (
    <svg
      className="pointer-events-none absolute inset-0 z-10"
      width={canvasWidth}
      height={canvasHeight}
      aria-hidden="true"
    >
      <defs>
        <style>{`
          .pine-edge {
            fill: none;
            stroke: rgba(255,255,255,0.12);
            stroke-width: 1.2;
            transition: stroke 0.25s, stroke-width 0.25s, opacity 0.25s;
          }
          .pine-edge-dimmed {
            opacity: 0.04;
          }
          .pine-edge-upstream {
            stroke: #4cd7f6;
            stroke-width: 2;
            stroke-dasharray: 6 7;
            filter: drop-shadow(0 0 5px rgba(76,215,246,0.6));
            animation: pineflow 1.1s linear infinite;
          }
          .pine-edge-downstream {
            stroke: #4edea3;
            stroke-width: 2;
            stroke-dasharray: 6 7;
            filter: drop-shadow(0 0 5px rgba(78,222,163,0.6));
            animation: pineflow 1.1s linear infinite reverse;
          }
          @keyframes pineflow {
            to { stroke-dashoffset: -13; }
          }
        `}</style>
      </defs>

      {edges.map((edge) => {
        const from = edge.from ?? edge.source ?? "";
        const to = edge.to ?? edge.target ?? "";
        const posFrom = positions.get(from);
        const posTo = positions.get(to);
        if (!posFrom || !posTo) return null;

        const key = edgeKey(from, to);
        const isUpstream = upstreamEdgeIds.has(key);
        const isDownstream = downstreamEdgeIds.has(key);
        const isLit = isUpstream || isDownstream;
        const isDimmed = isFocusing && !isLit;

        // Quadratic bezier control point: midpoint pulled slightly toward center
        const cx = (posFrom.x + posTo.x) / 2;
        const cy = (posFrom.y + posTo.y) / 2 + (posTo.y < posFrom.y ? -20 : 20);

        const d = `M${posFrom.x} ${posFrom.y} Q ${cx} ${cy} ${posTo.x} ${posTo.y}`;

        let className = "pine-edge";
        if (isDimmed) className += " pine-edge-dimmed";
        else if (isUpstream) className += " pine-edge-upstream";
        else if (isDownstream) className += " pine-edge-downstream";

        return (
          <path
            key={key}
            className={className}
            d={d}
          />
        );
      })}
    </svg>
  );
}
