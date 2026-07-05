export type NodeStatus = "locked" | "unlocked" | "completed";

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  answer_index?: number;
}

export interface Quiz {
  id: string;
  pass_threshold: number;
  questions: QuizQuestion[];
}

export interface RawTreeNode {
  id: string;
  name?: string;
  title?: string;
  level: number;
  status?: string;
  quiz?: Quiz;
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
  quiz?: Quiz;
}
