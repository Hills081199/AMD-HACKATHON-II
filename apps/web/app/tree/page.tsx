"use client";

import "@xyflow/react/dist/style.css";

import { useEffect, useMemo, useState } from "react";
import { Background, Controls, ReactFlow, type Edge, type NodeMouseHandler } from "@xyflow/react";

import { layoutNodesByLevel } from "./positions";
import { useTreeProgressStore } from "./progressStore";
import { QuizModal, type QuizResult } from "./QuizModal";
import { TreeNode, type TreeFlowNode } from "./TreeNode";
import type { TreeResponse } from "./types";
import { seedCompletedIds, toDisplayNodes } from "./unlock";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
// No topic-selection UI yet — this mirrors the topic_id used in
// apps/api/tests/test_trees_endpoint.py, which currently serves the same
// static sample dataset regardless of which topic_id is requested.
const TOPIC_ID = "intro-to-ml";

const nodeTypes = { concept: TreeNode };

export default function TreePage() {
  const [tree, setTree] = useState<TreeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const completedIds = useTreeProgressStore((state) => state.completedIds);
  const seedCompleted = useTreeProgressStore((state) => state.seedCompleted);
  const markCompleted = useTreeProgressStore((state) => state.markCompleted);

  const [quizNodeId, setQuizNodeId] = useState<string | null>(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [quizError, setQuizError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/trees/${TOPIC_ID}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`GET /trees/${TOPIC_ID} failed: ${response.status}`);
        }
        return response.json() as Promise<TreeResponse>;
      })
      .then((data) => {
        setTree(data);
        seedCompleted(seedCompletedIds(data.nodes));
      })
      .catch((err: Error) => setError(err.message));
  }, [seedCompleted]);

  const { flowNodes, flowEdges } = useMemo(() => {
    if (!tree) {
      return { flowNodes: [] as TreeFlowNode[], flowEdges: [] as Edge[] };
    }
    const displayNodes = toDisplayNodes(tree.nodes, tree.edges, completedIds);
    const positions = layoutNodesByLevel(displayNodes);

    const nextFlowNodes: TreeFlowNode[] = displayNodes.map((node) => ({
      id: node.id,
      type: "concept",
      position: positions.get(node.id) ?? { x: 0, y: 0 },
      data: { label: node.label, status: node.status },
    }));

    const nextFlowEdges: Edge[] = tree.edges.map((edge) => ({
      id: `${edge.from}->${edge.to}`,
      source: edge.from,
      target: edge.to,
    }));

    return { flowNodes: nextFlowNodes, flowEdges: nextFlowEdges };
  }, [tree, completedIds]);

  // Clicking an unlocked node with a checkpoint quiz opens it; completed and
  // locked nodes don't respond to clicks (locked has nothing to do yet,
  // completed already passed its quiz).
  const handleNodeClick: NodeMouseHandler<TreeFlowNode> = (_event, node) => {
    if (node.data.status !== "unlocked") {
      return;
    }
    const rawNode = tree?.nodes.find((candidate) => candidate.id === node.id);
    if (!rawNode?.quiz) {
      return;
    }
    setQuizNodeId(node.id);
    setQuizResult(null);
    setQuizError(null);
  };

  const closeQuiz = () => {
    setQuizNodeId(null);
    setQuizResult(null);
    setQuizError(null);
  };

  const submitQuiz = async (nodeId: string, answers: Record<string, number>) => {
    setQuizSubmitting(true);
    setQuizError(null);
    try {
      const response = await fetch(`${API_URL}/trees/${TOPIC_ID}/nodes/${nodeId}/submit-quiz`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
      });
      if (!response.ok) {
        throw new Error(`submit-quiz failed: ${response.status}`);
      }
      const body = (await response.json()) as QuizResult;
      setQuizResult(body);
      if (body.passed) {
        markCompleted(nodeId);
      }
    } catch (err) {
      setQuizError(err instanceof Error ? err.message : "Could not submit the quiz.");
    } finally {
      setQuizSubmitting(false);
    }
  };

  const quizNode = quizNodeId ? tree?.nodes.find((candidate) => candidate.id === quizNodeId) : undefined;

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <p className="text-red-600">Could not load the mastery tree: {error}</p>
      </main>
    );
  }

  if (!tree) {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <p className="text-neutral-500">Loading mastery tree…</p>
      </main>
    );
  }

  return (
    <main className="h-screen w-screen">
      <ReactFlow nodes={flowNodes} edges={flowEdges} nodeTypes={nodeTypes} onNodeClick={handleNodeClick} fitView>
        <Background />
        <Controls />
      </ReactFlow>
      {quizNode?.quiz && (
        <QuizModal
          nodeLabel={quizNode.title ?? quizNode.name ?? quizNode.id}
          quiz={quizNode.quiz}
          submitting={quizSubmitting}
          result={quizResult}
          error={quizError}
          onSubmit={(answers) => submitQuiz(quizNode.id, answers)}
          onClose={closeQuiz}
        />
      )}
    </main>
  );
}
