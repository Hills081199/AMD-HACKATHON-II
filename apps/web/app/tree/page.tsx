"use client";

import "@xyflow/react/dist/style.css";

import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { Controls, ReactFlow, type Edge, type NodeMouseHandler } from "@xyflow/react";
import { CircleUserRound, FileText, Network, Settings2, Workflow } from "lucide-react";

import { layoutNodesByLevel } from "./positions";
import { useTreeProgressStore } from "./progressStore";
import { QuizModal, type QuizResult } from "./QuizModal";
import { TreeNode, type TreeFlowNode } from "./TreeNode";
import type { NodeSource, NodeStatus, TreeResponse } from "./types";
import { deriveNodeStatuses, seedCompletedIds, toDisplayNodes } from "./unlock";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
// No topic-selection UI yet — this mirrors the topic_id used in
// apps/api/tests/test_trees_endpoint.py, which currently serves the same
// static sample dataset regardless of which topic_id is requested.
const TOPIC_ID = "intro-to-ml";

const nodeTypes = { concept: TreeNode };

// Matches stitch_atlas_learning_path_graph/atlas_your_mastery_tree's
// .connector-line / .connector-line-active / .connector-line-completed.
const EDGE_STYLE_BY_TARGET_STATUS: Record<NodeStatus, CSSProperties> = {
  locked: { stroke: "rgba(255,255,255,0.25)", strokeWidth: 2 },
  unlocked: {
    stroke: "#4cd7f6",
    strokeWidth: 2,
    filter: "drop-shadow(0 0 5px rgba(76,215,246,0.5))",
  },
  completed: { stroke: "#4edea3", strokeWidth: 2 },
};

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
    const statusById = deriveNodeStatuses(tree.nodes, tree.edges, completedIds);
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
      style: EDGE_STYLE_BY_TARGET_STATUS[statusById.get(edge.to) ?? "locked"],
    }));

    return { flowNodes: nextFlowNodes, flowEdges: nextFlowEdges };
  }, [tree, completedIds]);

  const sourceDocs = useMemo(() => {
    if (!tree) {
      return [] as NodeSource[];
    }
    const byDocId = new Map<string, NodeSource>();
    for (const node of tree.nodes) {
      for (const source of node.sources ?? []) {
        if (!byDocId.has(source.doc_id)) {
          byDocId.set(source.doc_id, source);
        }
      }
    }
    return [...byDocId.values()];
  }, [tree]);

  const percentComplete = tree && tree.nodes.length > 0 ? Math.round((completedIds.size / tree.nodes.length) * 100) : 0;

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
      <main className="flex min-h-screen items-center justify-center bg-surface p-8">
        <p className="text-error">Could not load the mastery tree: {error}</p>
      </main>
    );
  }

  if (!tree) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface p-8">
        <p className="text-on-surface-variant">Loading mastery tree…</p>
      </main>
    );
  }

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-surface text-on-surface">
      <header className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/10 bg-surface/70 px-margin-mobile shadow-sm backdrop-blur-xl md:px-margin-desktop">
        <h1 className="text-headline-lg font-bold tracking-tight text-on-surface">Atlas</h1>
        <button
          aria-label="Account"
          className="flex items-center justify-center text-primary transition-colors duration-200 hover:text-secondary"
        >
          <CircleUserRound size={24} />
        </button>
      </header>

      <div className="flex flex-1 pt-16">
        <nav className="fixed left-0 top-16 z-40 hidden h-[calc(100vh-64px)] w-64 flex-col border-r border-white/10 bg-surface/70 py-6 text-label-caps backdrop-blur-xl md:flex">
          <div className="mb-8 flex flex-col gap-2 px-6">
            <div className="mb-2 flex h-12 w-12 items-center justify-center rounded bg-primary-container/20 text-primary">
              <Workflow size={24} />
            </div>
            <h2 className="text-headline-lg-mobile text-xl text-on-surface">Mastery Hub</h2>
            <p className="text-tertiary">{percentComplete}% Complete</p>
          </div>
          <ul className="flex flex-1 flex-col">
            <li>
              <span className="flex items-center gap-4 border-r-2 border-secondary bg-primary-container/20 px-6 py-3 text-secondary">
                <Network size={20} />
                Learning Path
              </span>
            </li>
            <li>
              <span className="flex cursor-not-allowed items-center gap-4 px-6 py-3 text-on-surface-variant/40">
                <FileText size={20} />
                Documents
              </span>
            </li>
            <li>
              <span className="flex cursor-not-allowed items-center gap-4 px-6 py-3 text-on-surface-variant/40">
                <Settings2 size={20} />
                Settings
              </span>
            </li>
          </ul>
        </nav>

        <main className="relative flex-1 overflow-auto bg-surface-container-lowest bg-graph-pattern p-margin-mobile md:ml-64 md:p-margin-desktop">
          <div className="mx-auto flex h-full max-w-container-max flex-col gap-gutter md:flex-row">
            <div className="relative min-h-[600px] flex-1">
              <ReactFlow
                nodes={flowNodes}
                edges={flowEdges}
                nodeTypes={nodeTypes}
                onNodeClick={handleNodeClick}
                proOptions={{ hideAttribution: true }}
                fitView
              >
                <Controls />
              </ReactFlow>
            </div>

            <aside className="flex w-full shrink-0 flex-col gap-gutter md:w-80">
              <div className="glass-panel flex flex-col gap-4 rounded-xl p-6">
                <h3 className="text-headline-lg-mobile text-on-surface">Path Progress</h3>
                <div className="flex items-end gap-2">
                  <span className="text-display-lg text-tertiary">{percentComplete}%</span>
                  <span className="pb-2 text-stats-mono text-on-surface-variant">Completed</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-surface-container-high">
                  <div
                    className="h-full rounded-full bg-tertiary transition-all"
                    style={{ width: `${percentComplete}%` }}
                  />
                </div>
              </div>

              <div className="glass-panel flex flex-1 flex-col gap-4 rounded-xl p-6">
                <h3 className="text-headline-lg-mobile text-on-surface">Source Documents</h3>
                <div className="flex flex-col gap-3 text-stats-mono">
                  {sourceDocs.length === 0 && (
                    <p className="text-on-surface-variant">No source documents recorded yet.</p>
                  )}
                  {sourceDocs.map((source) => (
                    <div
                      key={source.doc_id}
                      className="flex items-center gap-3 rounded border border-white/5 bg-surface-container-low p-3 transition-colors hover:border-secondary/50"
                    >
                      <FileText size={20} className="shrink-0 text-primary" />
                      <div className="flex flex-col overflow-hidden">
                        <span className="truncate text-on-surface">{source.title ?? source.doc_id}</span>
                        {source.page != null && <span className="text-xs text-outline">Page {source.page}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </div>
        </main>
      </div>

      {quizNode?.quiz && (
        <QuizModal
          nodeLabel={quizNode.title ?? quizNode.name ?? quizNode.id}
          quiz={quizNode.quiz}
          lesson={quizNode.lesson}
          submitting={quizSubmitting}
          result={quizResult}
          error={quizError}
          onSubmit={(answers) => submitQuiz(quizNode.id, answers)}
          onClose={closeQuiz}
        />
      )}
    </div>
  );
}
