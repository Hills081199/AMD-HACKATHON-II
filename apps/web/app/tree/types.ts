export type NodeStatus = "locked" | "unlocked" | "completed";

export interface RawTreeNode {
  id: string;
  name?: string;
  title?: string;
  level: number;
  status?: string;
}

export interface TreeEdge {
  from: string;
  to: string;
  confidence?: number;
}

export interface TreeResponse {
  nodes: RawTreeNode[];
  edges: TreeEdge[];
}

export interface DisplayNode {
  id: string;
  label: string;
  level: number;
  status: NodeStatus;
}
