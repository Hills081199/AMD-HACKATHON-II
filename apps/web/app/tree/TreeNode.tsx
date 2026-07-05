"use client";

import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";

import type { NodeStatus } from "./types";

export interface TreeNodeFields extends Record<string, unknown> {
  label: string;
  status: NodeStatus;
}

export type TreeFlowNode = Node<TreeNodeFields, "concept">;

const STATUS_STYLES: Record<NodeStatus, string> = {
  locked: "bg-locked/10 border-locked text-neutral-400 cursor-not-allowed",
  unlocked: "bg-unlocked/10 border-unlocked text-neutral-900 cursor-pointer",
  completed: "bg-completed/10 border-completed text-neutral-900 cursor-pointer",
};

export function TreeNode({ data }: NodeProps<TreeFlowNode>) {
  return (
    <div
      className={`rounded-lg border-2 px-4 py-2 text-sm font-medium shadow-sm transition-colors ${STATUS_STYLES[data.status]}`}
    >
      <Handle type="target" position={Position.Left} />
      {data.label}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
