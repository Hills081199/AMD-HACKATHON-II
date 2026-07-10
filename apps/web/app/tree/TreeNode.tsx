"use client";

import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { CheckCircle2, Lock, TrendingUp } from "lucide-react";

import type { NodeStatus } from "./types";

export interface TreeNodeFields extends Record<string, unknown> {
  label: string;
  status: NodeStatus;
}

export type TreeFlowNode = Node<TreeNodeFields, "concept">;

// Matches stitch_atlas_learning_path_graph/atlas_your_mastery_tree's
// .node-completed / .node-active / .node-locked classes.
const STATUS_STYLES: Record<NodeStatus, string> = {
  locked: "border border-dashed border-white/40 bg-transparent text-white/40 cursor-not-allowed",
  unlocked: "border border-secondary bg-secondary/10 text-on-surface glow-active cursor-pointer",
  completed: "border border-tertiary bg-tertiary text-on-tertiary shadow-lg cursor-pointer",
};

const STATUS_ICONS: Record<NodeStatus, typeof CheckCircle2> = {
  locked: Lock,
  unlocked: TrendingUp,
  completed: CheckCircle2,
};

export function TreeNode({ data }: NodeProps<TreeFlowNode>) {
  const Icon = STATUS_ICONS[data.status];
  return (
    <div
      className={`flex w-48 flex-col items-center justify-center rounded-xl p-4 text-center text-label-caps transition-transform hover:scale-105 ${STATUS_STYLES[data.status]}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-outline-variant" />
      <Icon size={24} className="mb-2" strokeWidth={2} />
      <span>{data.label}</span>
      <Handle type="source" position={Position.Right} className="!bg-outline-variant" />
    </div>
  );
}
