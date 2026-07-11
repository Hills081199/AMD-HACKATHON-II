"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Minus, Plus, RotateCcw } from "lucide-react";
import type { DisplayNode, TreeEdge } from "./types";
import type { PineLayout } from "./pineLayout";
import { EdgeLayer } from "./EdgeLayer";
import { PineTreeNode } from "./PineTreeNode";

const MIN_ZOOM = 0.3;
const MAX_ZOOM = 2;
const ZOOM_STEP = 0.15;

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

/**
 * Simple unified Christmas tree - single smooth shape
 * Uses SVG for smooth curves like the reference image
 */
function PineFoliage({
  canvasHeight,
  canvasWidth,
  trunkTop,
  treeTop,
  nodesWidth
}: {
  canvasHeight: number;
  canvasWidth: number;
  trunkTop: number;   // Y position where trunk meets foliage (bottom of leaves)
  treeTop: number;    // Y position of tree top
  nodesWidth: number; // Width of level 0 nodes spread
}) {
  // Tree dimensions calculated from actual node positions
  const treeHeight = trunkTop - treeTop + 60; // Add padding above top node
  // Make tree wide enough to cover all nodes with generous padding on sides
  const treeWidth = Math.max(nodesWidth + 350, canvasWidth * 0.92);
  const centerX = canvasWidth / 2;
  const treeBottom = canvasHeight - trunkTop - 30; // Lower the tree base to cover bottom nodes

  // SVG path for smooth Christmas tree silhouette
  // Starts at top point, curves down with wavy edges
  const treePath = `
    M 50 0
    Q 52 3, 55 5
    Q 65 12, 58 15
    Q 72 22, 62 26
    Q 80 35, 66 40
    Q 88 52, 70 58
    Q 95 72, 75 78
    Q 100 90, 80 94
    L 100 100
    L 0 100
    L 20 94
    Q 0 90, 25 78
    Q 5 72, 30 58
    Q 12 52, 34 40
    Q 20 35, 38 26
    Q 28 22, 42 15
    Q 35 12, 45 5
    Q 48 3, 50 0
    Z
  `;

  return (
    <div className="pointer-events-none absolute inset-0 z-0" aria-hidden="true">
      {/* Main tree shape using SVG for smooth curves */}
      <svg
        style={{
          position: "absolute",
          left: centerX - treeWidth / 2,
          bottom: treeBottom,
          width: treeWidth,
          height: treeHeight,
        }}
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <defs>
          {/* Main gradient */}
          <linearGradient id="treeGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#2d7a50" />
            <stop offset="30%" stopColor="#236b45" />
            <stop offset="60%" stopColor="#1a5c3a" />
            <stop offset="100%" stopColor="#144d30" />
          </linearGradient>
          {/* Highlight gradient */}
          <radialGradient id="treeHighlight" cx="50%" cy="30%" r="50%">
            <stop offset="0%" stopColor="rgba(100,200,140,0.3)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
          {/* Shadow filter */}
          <filter id="treeShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="10" stdDeviation="15" floodColor="rgba(0,30,20,0.4)" />
          </filter>
        </defs>

        {/* Tree body */}
        <path
          d={treePath}
          fill="url(#treeGradient)"
          filter="url(#treeShadow)"
        />

        {/* Highlight overlay */}
        <path
          d={treePath}
          fill="url(#treeHighlight)"
        />
      </svg>

      {/* Star glow at top */}
      <div
        style={{
          position: "absolute",
          left: centerX - 50,
          bottom: treeBottom + treeHeight - 20,
          width: 100,
          height: 100,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(255,230,150,0.5) 0%, rgba(255,200,80,0.2) 40%, transparent 70%)",
          animation: "star-glow 2.5s ease-in-out infinite",
        }}
      />
      <style>{`
        @keyframes star-glow {
          0%, 100% { opacity: 0.7; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.1); }
        }
      `}</style>
    </div>
  );
}

/** Trunk and ground decoration at the very bottom */
function PineTrunk({ canvasWidth, canvasHeight }: { canvasWidth: number; canvasHeight: number }) {
  return (
    <div className="pointer-events-none absolute z-0" aria-hidden="true" style={{ left: 0, right: 0, bottom: 0, height: 220 }}>
      {/* Ground glow */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: 70,
          width: 900,
          height: 80,
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
          bottom: 118,
          width: 46,
          height: 150,
          transform: "translateX(-50%)",
          borderRadius: "10px 10px 4px 4px",
          background: "linear-gradient(180deg,#5a4030,#3a2a1e)",
          boxShadow: "inset 6px 0 10px rgba(0,0,0,0.33), inset -6px 0 10px rgba(0,0,0,0.25)",
        }}
      />
      {/* Root label */}
      <div
        className="text-label-caps text-on-surface-variant/50 tracking-widest absolute"
        style={{ left: "50%", bottom: 66, transform: "translateX(-50%)", whiteSpace: "nowrap" }}
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
  const [zoom, setZoom] = useState(1);

  // Zoom controls
  const zoomIn = useCallback(() => {
    setZoom((z) => Math.min(MAX_ZOOM, z + ZOOM_STEP));
  }, []);

  const zoomOut = useCallback(() => {
    setZoom((z) => Math.max(MIN_ZOOM, z - ZOOM_STEP));
  }, []);

  const resetZoom = useCallback(() => {
    setZoom(1);
  }, []);

  // Handle mouse wheel zoom
  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;

    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
        setZoom((z) => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, z + delta)));
      }
    };

    wrapper.addEventListener("wheel", handleWheel, { passive: false });
    return () => wrapper.removeEventListener("wheel", handleWheel);
  }, []);

  // Find the node at the highest level (treetop)
  const topNode = nodes.reduce<DisplayNode | null>((acc, n) => {
    if (!acc || n.level > acc.level) return n;
    return acc;
  }, null);

  const topPos = topNode ? positions.get(topNode.id) : null;

  // Find bottom and top Y positions for tree background alignment
  // Level 0 nodes are at the bottom, highest level at top
  const bottomNode = nodes.reduce<DisplayNode | null>((acc, n) => {
    if (!acc || n.level < acc.level) return n;
    return acc;
  }, null);
  const bottomPos = bottomNode ? positions.get(bottomNode.id) : null;

  // trunkTop = Y position of level 0 nodes (bottom of tree foliage)
  // treeTop = Y position of highest level node (top of tree)
  const trunkTopY = bottomPos?.y ?? (canvasHeight - 220);
  const treeTopY = topPos?.y ?? 80;

  // Calculate width of level 0 nodes (widest spread)
  const level0Nodes = nodes.filter(n => n.level === 0);
  const level0Positions = level0Nodes.map(n => positions.get(n.id)).filter(Boolean) as { x: number; y: number }[];
  const minX = level0Positions.length > 0 ? Math.min(...level0Positions.map(p => p.x)) : canvasWidth * 0.15;
  const maxX = level0Positions.length > 0 ? Math.max(...level0Positions.map(p => p.x)) : canvasWidth * 0.85;
  const nodesWidth = maxX - minX;

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
      {/* Zoom controls */}
      <div className="absolute right-4 top-4 z-30 flex flex-col gap-1">
        <button
          onClick={(e) => { e.stopPropagation(); zoomIn(); }}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-surface-container/80 text-on-surface-variant backdrop-blur-md transition-colors hover:bg-surface-container-high hover:text-on-surface"
          title="Zoom in (Ctrl + Scroll)"
        >
          <Plus size={18} />
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); zoomOut(); }}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-surface-container/80 text-on-surface-variant backdrop-blur-md transition-colors hover:bg-surface-container-high hover:text-on-surface"
          title="Zoom out (Ctrl + Scroll)"
        >
          <Minus size={18} />
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); resetZoom(); }}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-surface-container/80 text-on-surface-variant backdrop-blur-md transition-colors hover:bg-surface-container-high hover:text-on-surface"
          title="Reset zoom"
        >
          <RotateCcw size={16} />
        </button>
        <div className="mt-1 rounded-md bg-surface-container/80 px-2 py-1 text-center text-xs text-on-surface-variant backdrop-blur-md">
          {Math.round(zoom * 100)}%
        </div>
      </div>

      <div
        className="relative origin-top-left transition-transform duration-150"
        style={{
          width: canvasWidth,
          height: canvasHeight,
          minWidth: canvasWidth,
          transform: `scale(${zoom})`,
          transformOrigin: "center top",
        }}
      >
        {/* Pine foliage decorative background - single unified tree */}
        <PineFoliage
          canvasHeight={canvasHeight}
          canvasWidth={canvasWidth}
          trunkTop={trunkTopY + 30}
          treeTop={treeTopY - 40}
          nodesWidth={nodesWidth}
        />

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
