"use client";

import { useCallback, useEffect, useRef } from "react";
import type { DisplayNode, TreeEdge } from "./types";
import type { PineLayout } from "./pineLayout";
import { EdgeLayer } from "./EdgeLayer";
import { PineTreeNode } from "./PineTreeNode";

interface PineCanvasProps {
  nodes: DisplayNode[];
  edges: TreeEdge[];
  layout: PineLayout;
  isFocusing: boolean;
  hoveredId: string | null;
  selectedId: string | null;
  litNodeIds: Set<string>;
  upstreamEdgeIds: Set<string>;
  downstreamEdgeIds: Set<string>;
  onHoverNode: (id: string | null) => void;
  onClickNode: (id: string) => void;
  onClickCanvas: () => void;
  scrollToRef: React.MutableRefObject<((nodeId: string) => void) | null>;
}

/** Decorative pine foliage tiers rendered as CSS clip-path polygons */
function PineFoliage({ canvasHeight, numTiers }: { canvasHeight: number; numTiers: number }) {
  // Pine polygon clip-path - smoother pine shape
  const pineClip = "polygon(50% 0%, 55% 20%, 75% 25%, 62% 45%, 85% 52%, 72% 70%, 95% 80%, 78% 90%, 100% 100%, 0% 100%, 22% 90%, 5% 80%, 28% 70%, 15% 52%, 38% 45%, 25% 25%, 45% 20%)";

  // Dynamic tiers based on canvas height - more compact spacing
  const baseTiers = [
    { widthPx: 1000, heightPx: 220, opacity: 0.75, bottomOffset: 160 },
    { widthPx: 800, heightPx: 200, opacity: 0.8, bottomOffset: 320 },
    { widthPx: 620, heightPx: 180, opacity: 0.85, bottomOffset: 460 },
    { widthPx: 460, heightPx: 160, opacity: 0.88, bottomOffset: 580 },
    { widthPx: 320, heightPx: 140, opacity: 0.9, bottomOffset: 680 },
    { widthPx: 200, heightPx: 120, opacity: 0.92, bottomOffset: 770 },
  ];

  // Filter tiers that fit within canvas
  const tiers = baseTiers.filter(t => t.bottomOffset + t.heightPx < canvasHeight - 40).slice(0, Math.min(numTiers, 6));

  return (
    <div className="pointer-events-none absolute inset-0 z-0" aria-hidden="true">
      {tiers.map((tier, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: "50%",
            bottom: tier.bottomOffset,
            width: tier.widthPx,
            height: tier.heightPx,
            transform: "translateX(-50%)",
            clipPath: pineClip,
            background:
              "repeating-linear-gradient(115deg,rgba(63,174,124,0.07) 0 3px,transparent 3px 11px)," +
              "repeating-linear-gradient(65deg,rgba(111,227,165,0.06) 0 2px,transparent 2px 13px)," +
              "linear-gradient(180deg,rgba(23,69,52,0.4),rgba(15,47,42,0.33) 60%,rgba(12,38,31,0.27))",
            filter: "drop-shadow(0 18px 22px rgba(4,18,26,0.53))",
            opacity: tier.opacity,
          }}
        />
      ))}

      {/* Decorative leaf sprigs */}
      {[
        { left: -30, bottom: 100, rotate: 0, scaleX: 1 },
        { left: "auto" as const, right: -40, bottom: 180, rotate: 0, scaleX: -1 },
      ].map((pos, i) => (
        <div
          key={`sprig-${i}`}
          style={{
            position: "absolute",
            ...(pos.left !== "auto" ? { left: pos.left } : { right: (pos as typeof pos & { right: number }).right }),
            bottom: pos.bottom,
            width: 200,
            height: 200,
            opacity: 0.45,
            transform: `scaleX(${pos.scaleX})`,
            background:
              "repeating-linear-gradient(25deg,rgba(63,174,124,0.11) 0 2px,transparent 2px 10px)," +
              "repeating-linear-gradient(-35deg,rgba(111,227,165,0.07) 0 2px,transparent 2px 12px)",
            clipPath: "polygon(0 100%,45% 55%,30% 50%,60% 30%,50% 25%,100% 0,70% 45%,80% 50%,55% 68%,65% 74%,20% 100%)",
          }}
        />
      ))}
    </div>
  );
}

/** Trunk and ground decoration at the very bottom */
function PineTrunk({ canvasWidth, canvasHeight }: { canvasWidth: number; canvasHeight: number }) {
  return (
    <div className="pointer-events-none absolute z-0" aria-hidden="true" style={{ left: 0, right: 0, bottom: 0, height: 180 }}>
      {/* Ground glow */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: 50,
          width: 700,
          height: 60,
          transform: "translateX(-50%)",
          borderRadius: "50%",
          background: "radial-gradient(closest-side,rgba(22,50,68,0.35),transparent 70%)",
        }}
      />
      {/* Trunk */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: 90,
          width: 40,
          height: 120,
          transform: "translateX(-50%)",
          borderRadius: "8px 8px 4px 4px",
          background: "linear-gradient(180deg,#5a4030,#3a2a1e)",
          boxShadow: "inset 5px 0 8px rgba(0,0,0,0.33), inset -5px 0 8px rgba(0,0,0,0.25)",
        }}
      />
      {/* Root label */}
      <div
        className="text-label-caps text-on-surface-variant/50 tracking-widest absolute"
        style={{ left: "50%", bottom: 50, transform: "translateX(-50%)", whiteSpace: "nowrap", fontSize: "11px" }}
      >
        Roots · Level 0
      </div>
    </div>
  );
}

/** Treetop star glow at the highest-level node position */
function TreetopStar({ x, y }: { x: number; y: number }) {
  return (
    <div
      className="pointer-events-none absolute z-0"
      style={{ left: x, top: y, transform: "translate(-50%,-50%)" }}
      aria-hidden="true"
    >
      <div
        style={{
          width: 120,
          height: 120,
          borderRadius: "50%",
          transform: "translate(-50%,-50%)",
          background: "radial-gradient(closest-side,rgba(255,222,158,0.33),transparent 70%)",
          animation: "pinetop-twinkle 2.6s ease-in-out infinite",
        }}
      />
      <style>{`
        @keyframes pinetop-twinkle {
          0%,100% { opacity:0.55; transform:translate(-50%,-50%) scale(1); }
          50% { opacity:1; transform:translate(-50%,-50%) scale(1.18); }
        }
      `}</style>
    </div>
  );
}

export function PineCanvas({
  nodes,
  edges,
  layout,
  isFocusing,
  hoveredId,
  selectedId,
  litNodeIds,
  upstreamEdgeIds,
  downstreamEdgeIds,
  onHoverNode,
  onClickNode,
  onClickCanvas,
  scrollToRef,
}: PineCanvasProps) {
  const { positions, canvasWidth, canvasHeight, maxLevel, numTiers } = layout;
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Find the node at the highest level (treetop)
  const topNode = nodes.reduce<DisplayNode | null>((acc, n) => {
    if (!acc || n.level > acc.level) return n;
    return acc;
  }, null);

  const topPos = topNode ? positions.get(topNode.id) : null;

  // Expose scrollToNode via ref
  const scrollToNode = useCallback(
    (nodeId: string) => {
      const pos = positions.get(nodeId);
      if (!pos || !wrapperRef.current) return;
      const wrapper = wrapperRef.current;
      const scrollLeft = pos.x - wrapper.clientWidth / 2;
      const scrollTop = pos.y - wrapper.clientHeight / 2;
      wrapper.scrollTo({ left: scrollLeft, top: scrollTop, behavior: "smooth" });
    },
    [positions]
  );

  useEffect(() => {
    scrollToRef.current = scrollToNode;
  }, [scrollToNode, scrollToRef]);

  return (
    <div
      ref={wrapperRef}
      className="relative flex-1 overflow-auto"
      onClick={onClickCanvas}
      style={{ background: "transparent" }}
    >
      <div
        className="relative"
        style={{ width: canvasWidth, height: canvasHeight, minWidth: canvasWidth }}
      >
        {/* Pine foliage decorative background */}
        <PineFoliage canvasHeight={canvasHeight} numTiers={numTiers} />

        {/* Treetop glow */}
        {topPos && <TreetopStar x={topPos.x} y={topPos.y} />}

        {/* Trunk + ground */}
        <PineTrunk canvasWidth={canvasWidth} canvasHeight={canvasHeight} />

        {/* SVG edges */}
        <EdgeLayer
          edges={edges}
          layout={layout}
          isFocusing={isFocusing}
          upstreamEdgeIds={upstreamEdgeIds}
          downstreamEdgeIds={downstreamEdgeIds}
        />

        {/* HTML nodes */}
        {nodes.map((node) => {
          const pos = positions.get(node.id);
          if (!pos) return null;
          const isLit = litNodeIds.has(node.id);
          const isSelf = node.id === hoveredId || node.id === selectedId;
          const isTopNode = node.id === topNode?.id;
          return (
            <PineTreeNode
              key={node.id}
              node={node}
              x={pos.x}
              y={pos.y}
              maxLevel={maxLevel}
              isLit={isLit}
              isSelf={isSelf}
              isFocusing={isFocusing}
              isTopNode={isTopNode}
              onHover={onHoverNode}
              onClick={onClickNode}
            />
          );
        })}
      </div>
    </div>
  );
}
