"use client";

import { CheckCircle2, Lock, Star, TrendingUp } from "lucide-react";
import type { DisplayNode, NodeStatus } from "./types";

export type PineTier = "foundational" | "intermediate" | "advanced";

export function getTier(level: number, maxLevel: number): PineTier {
  if (level === 0) return "foundational";
  if (maxLevel <= 1 || level <= Math.floor(maxLevel / 2)) return "intermediate";
  return "advanced";
}

interface PineTreeNodeProps {
  node: DisplayNode;
  x: number;
  y: number;
  maxLevel: number;
  isLit: boolean;
  isSelf: boolean;
  isFocusing: boolean;
  isTopNode: boolean;
  onHover: (id: string | null) => void;
  onClick: (id: string) => void;
}

const TIER_DOT_COLORS: Record<PineTier, string> = {
  foundational: "bg-secondary shadow-[0_0_12px_rgba(76,215,246,0.8)]",
  intermediate: "bg-tertiary shadow-[0_0_12px_rgba(78,222,163,0.8)]",
  advanced: "bg-primary shadow-[0_0_14px_rgba(192,193,255,0.9)]",
};

// Completed node uses a golden/amber color to indicate mastery
const COMPLETED_DOT_COLOR = "bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.8)]";
const COMPLETED_TEXT_COLOR = "text-amber-400";

const TIER_TEXT_COLORS: Record<PineTier, string> = {
  foundational: "text-secondary",
  intermediate: "text-tertiary",
  advanced: "text-primary",
};

const TIER_RING_COLORS: Record<PineTier, string> = {
  foundational: "border-secondary/60",
  intermediate: "border-tertiary/60",
  advanced: "border-primary/60",
};

const STATUS_ICONS: Record<NodeStatus, typeof CheckCircle2> = {
  locked: Lock,
  unlocked: TrendingUp,
  completed: CheckCircle2,
};

/**
 * Pine tree node rendered as an absolutely-positioned div.
 * Uses a small dot + label approach matching the reference design,
 * with framer-motion-inspired CSS transitions for smooth interactions.
 */
export function PineTreeNode({
  node,
  x,
  y,
  maxLevel,
  isLit,
  isSelf,
  isFocusing,
  isTopNode,
  onHover,
  onClick,
}: PineTreeNodeProps) {
  const tier = getTier(node.level, maxLevel);
  const Icon = STATUS_ICONS[node.status];
  const isLocked = node.status === "locked";
  const isCompleted = node.status === "completed";

  const dimmed = isFocusing && !isLit && !isSelf;
  const highlighted = isSelf;

  // Completed nodes use golden color, locked use gray, unlocked use tier color
  const dotClass = isLocked
    ? "bg-surface-container-high border border-dashed border-white/30 shadow-none"
    : isCompleted
    ? COMPLETED_DOT_COLOR
    : `${TIER_DOT_COLORS[tier]}`;

  const labelClass = isLocked
    ? "text-on-surface-variant/50"
    : highlighted
    ? `font-semibold ${isCompleted ? COMPLETED_TEXT_COLOR : TIER_TEXT_COLORS[tier]}`
    : isFocusing && isLit
    ? `${isCompleted ? COMPLETED_TEXT_COLOR : TIER_TEXT_COLORS[tier]}`
    : isCompleted
    ? COMPLETED_TEXT_COLOR
    : "text-on-surface-variant";

  const topNodeClasses = isTopNode
    ? "w-8 h-8 clip-star"
    : "w-5 h-5 rounded-full";

  return (
    <button
      style={{
        left: x,
        top: y,
        transform: "translate(-50%, -50%)",
        opacity: dimmed ? 0.18 : 1,
        transition: "opacity 0.25s, transform 0.2s",
        zIndex: highlighted ? 20 : isSelf ? 15 : 5,
      }}
      className={`absolute flex flex-col items-center gap-1.5 border-0 bg-transparent p-0 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary ${
        highlighted ? "scale-125 z-20" : "hover:scale-110"
      } transition-transform duration-200 cursor-pointer`}
      onMouseEnter={() => onHover(node.id)}
      onMouseLeave={() => onHover(null)}
      onClick={() => onClick(node.id)}
      aria-label={node.label}
      title={node.label}
    >
      {/* Dot */}
      <span className="relative flex items-center justify-center">
        <span
          className={`${isTopNode ? "w-8 h-8" : "w-5 h-5"} ${isTopNode ? "rounded-sm" : "rounded-full"} ${dotClass} flex items-center justify-center transition-all duration-200 ${
            highlighted ? "scale-125" : ""
          }`}
          style={
            isTopNode
              ? { clipPath: "polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%)" }
              : {}
          }
        >
          {isLocked && (
            <Lock size={9} className="text-outline/80" strokeWidth={2.5} />
          )}
          {isCompleted && !isTopNode && (
            <CheckCircle2 size={12} className="text-amber-900" strokeWidth={2.5} />
          )}
          {!isLocked && isTopNode && (
            <Star size={12} className="text-on-primary" strokeWidth={2} />
          )}
        </span>
        {/* Pulsing ring for unlocked nodes only (not completed) */}
        {node.status === "unlocked" && (
          <span
            className={`absolute inset-0 rounded-full border ${TIER_RING_COLORS[tier]} animate-ping opacity-50`}
            style={{ animationDuration: "2.4s" }}
          />
        )}
        {/* Self glow overlay */}
        {highlighted && (
          <span
            className="absolute -inset-2 rounded-full opacity-40 blur-sm"
            style={{ background: isLocked ? "transparent" : isCompleted ? "#fbbf24" : tier === "foundational" ? "#4cd7f6" : tier === "intermediate" ? "#4edea3" : "#c0c1ff" }}
          />
        )}
      </span>

      {/* Label */}
      <span
        className={`max-w-[118px] text-center text-[10.5px] leading-[1.25] transition-colors duration-200 ${labelClass}`}
        style={{ textShadow: "0 1px 3px rgba(0,0,0,0.8)" }}
      >
        {node.label}
      </span>
    </button>
  );
}
