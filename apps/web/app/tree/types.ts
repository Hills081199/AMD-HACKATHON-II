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

export interface NodeSource {
  doc_id: string;
  title?: string;
  page?: number;
  chunk_id?: string;
}

export interface NodeLesson {
  summary: string;
  real_world_example?: string;
}

export interface RawTreeNode {
  id: string;
  name?: string;
  title?: string;
  level: number;
  status?: string;
  quiz?: Quiz;
  lesson?: NodeLesson;
  sources?: NodeSource[];
}

export interface TreeEdge {
  from?: string;
  to?: string;
  // Backend may return source/target instead of from/to
  source?: string;
  target?: string;
  confidence?: number;
}

export interface TreeResponse {
  topic?: string;
  status?: string;
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
