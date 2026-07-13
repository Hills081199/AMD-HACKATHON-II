"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { FileText, Network, Workflow, Pencil, Trash2, Check, X } from "lucide-react";
import React from "react";

import { useRouter } from "next/navigation";
import { Header } from "../components/Header";
import { userApi, progressApi } from "../lib/api";
import { useAuth } from "../lib/auth-context";
import { QuizModal, type QuizResult } from "./QuizModal";
import { ChatPanel } from "./ChatPanel";
import { StatsStrip } from "./StatsStrip";
import { SearchBar } from "./SearchBar";
import { PineCanvas } from "./PineCanvas";
import { usePineInteraction } from "./usePineInteraction";
import { computePineLayout } from "./pineLayout";
import { clusterForDisplay } from "./clusterNodes";
import { useTreeProgressStore } from "./progressStore";
import { deriveNodeStatuses, seedCompletedIds, toDisplayNodes } from "./unlock";
import type { NodeSource, RawTreeNode, TreeResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEFAULT_TOPIC_ID = "intro-to-ml";

function TreePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuth();
  const topicId = searchParams.get("topic") || DEFAULT_TOPIC_ID;

  const [tree, setTree] = useState<TreeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const completedIds = useTreeProgressStore((state) => state.completedIds);
  const seedCompleted = useTreeProgressStore((state) => state.seedCompleted);
  const markCompleted = useTreeProgressStore((state) => state.markCompleted);

  const [quizNodeId, setQuizNodeId] = useState<string | null>(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [quizError, setQuizError] = useState<string | null>(null);

  // State for on-demand lesson/quiz generation
  const [isGenerating, setIsGenerating] = useState(false);

  // State for topic management (rename/delete)
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Ref that PineCanvas populates so SearchBar can scroll to a node
  const scrollToRef = useRef<((nodeId: string) => void) | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/trees/${topicId}`)
      .then((response) => {
        if (!response.ok) throw new Error(`GET /trees/${topicId} failed: ${response.status}`);
        return response.json() as Promise<TreeResponse>;
      })
      .then(async (data) => {
        setTree(data);

        // Try to load progress from backend if user is logged in
        if (user) {
          try {
            const progress = await progressApi.getProgress(topicId);
            // Merge backend progress with any node-level completed status
            const backendCompleted = new Set(progress.completed_node_ids);
            const localCompleted = seedCompletedIds(data.nodes);
            // Union of both sets
            const allCompleted = [...new Set([...localCompleted, ...backendCompleted])];
            seedCompleted(allCompleted);
          } catch {
            // If progress API fails (e.g., not logged in), fall back to local-only
            seedCompleted(seedCompletedIds(data.nodes));
          }
        } else {
          seedCompleted(seedCompletedIds(data.nodes));
        }
      })
      .catch((err: Error) => setError(err.message));
  }, [topicId, seedCompleted, user]);

  /** Update a single node in the tree state (after lesson/quiz generation) */
  const patchNode = useCallback((nodeId: string, patch: Partial<RawTreeNode>) => {
    setTree((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        nodes: prev.nodes.map((n) => (n.id === nodeId ? { ...n, ...patch } : n)),
      };
    });
  }, []);

  /** Call the backend to generate lesson + quiz for a node on demand.
   * Uses cache: if the node already has lesson.summary, skips the API call. */
  const generateLesson = useCallback(
    async (node: RawTreeNode) => {
      const alreadyHasContent =
        node.lesson?.summary && node.lesson.summary.trim().length > 0 &&
        node.quiz?.questions && node.quiz.questions.length > 0;

      if (alreadyHasContent) {
        // Content already available — open modal immediately, no generation needed
        return;
      }

      setIsGenerating(true);
      try {
        const response = await fetch(
          `${API_URL}/trees/${topicId}/nodes/${node.id}/generate-lesson`,
          { method: "POST" }
        );
        if (!response.ok) throw new Error(`generate-lesson failed: ${response.status}`);
        const body = await response.json();
        // Patch the node in local state so the modal re-renders with new content
        patchNode(node.id, {
          lesson: {
            summary: body.lesson ?? "",
            real_world_example: body.example ?? "",
          },
          quiz: body.quiz ?? null,
        });
      } catch (err) {
        console.error("[TreePage] generate-lesson error:", err);
        // Don't block the modal — just show empty content
      } finally {
        setIsGenerating(false);
      }
    },
    [topicId, patchNode]
  );

  // Derive display nodes + cluster if large
  const { allDisplayNodes, clusterResult } = useMemo(() => {
    if (!tree) return { allDisplayNodes: [], clusterResult: null };
    const allDisplayNodes = toDisplayNodes(tree.nodes, tree.edges, completedIds);
    const clusterResult = clusterForDisplay(allDisplayNodes, tree.edges);
    return { allDisplayNodes, clusterResult };
  }, [tree, completedIds]);

  // Layout computation (bottom-up pine positions)
  const layout = useMemo(() => {
    if (!clusterResult) return computePineLayout([]);
    return computePineLayout(clusterResult.displayNodes);
  }, [clusterResult]);

  // Interaction state (hover/click chain highlighting)
  const interaction = usePineInteraction(
    clusterResult?.displayNodes ?? [],
    clusterResult?.displayEdges ?? []
  );

  // Stats
  const numTiers = layout.numTiers;
  const statusById = useMemo(() => {
    if (!tree) return new Map<string, string>();
    return deriveNodeStatuses(tree.nodes, tree.edges, completedIds);
  }, [tree, completedIds]);

  const nodesUnlocked = [...statusById.values()].filter(
    (s) => s === "unlocked" || s === "completed"
  ).length;

  const percentComplete =
    tree && tree.nodes.length > 0
      ? Math.round((completedIds.size / tree.nodes.length) * 100)
      : 0;

  const sourceDocs = useMemo(() => {
    if (!tree) return [] as NodeSource[];
    const byDocId = new Map<string, NodeSource>();
    for (const node of tree.nodes) {
      for (const source of node.sources ?? []) {
        if (!byDocId.has(source.doc_id)) byDocId.set(source.doc_id, source);
      }
    }
    return [...byDocId.values()];
  }, [tree]);

  // Node click: open quiz OR select for chain highlight
  function handleNodeClick(nodeId: string) {
    interaction.onClickNode(nodeId);
    const status = statusById.get(nodeId);
    // Allow clicking on unlocked OR completed nodes (to review content)
    if (status === "unlocked" || status === "completed") {
      setQuizNodeId(nodeId);
      setQuizResult(null);
      setQuizError(null);

      // Find the raw node and trigger generation if needed
      const rawNode = tree?.nodes.find((n) => n.id === nodeId);
      if (rawNode) {
        // Only trigger if lesson is missing
        const alreadyHasContent =
          rawNode.lesson?.summary && rawNode.lesson.summary.trim().length > 0;
        if (!alreadyHasContent) {
          generateLesson(rawNode);
        }
      }
    }
  }

  const closeQuiz = () => {
    setQuizNodeId(null);
    setQuizResult(null);
    setQuizError(null);
    setIsGenerating(false);
  };

  const submitQuiz = async (nodeId: string, answers: Record<string, number>) => {
    setQuizSubmitting(true);
    setQuizError(null);
    try {
      const response = await fetch(
        `${API_URL}/trees/${topicId}/nodes/${nodeId}/submit-quiz`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answers }),
        }
      );
      if (!response.ok) throw new Error(`submit-quiz failed: ${response.status}`);
      const body = (await response.json()) as QuizResult;
      setQuizResult(body);
      if (body.passed) {
        markCompleted(nodeId);
        // Save progress to backend if user is logged in
        if (user) {
          try {
            await progressApi.saveProgress(topicId, nodeId, body.score);
          } catch (err) {
            // Non-fatal: progress is still saved locally
            console.warn("[TreePage] Could not save progress to backend:", err);
          }
        }
      }
    } catch (err) {
      setQuizError(err instanceof Error ? err.message : "Could not submit the quiz.");
    } finally {
      setQuizSubmitting(false);
    }
  };

  // Always read the latest node data from `tree`
  // We use useMemo to explicitly recalculate when `tree` changes.
  const quizNode = useMemo(() => {
    return quizNodeId ? tree?.nodes.find((n) => n.id === quizNodeId) : undefined;
  }, [quizNodeId, tree]);

  // Handle search selection: scroll + highlight
  function handleSearchSelect(nodeId: string) {
    interaction.onClickNode(nodeId);
    scrollToRef.current?.(nodeId);
  }

  // Topic management handlers
  const handleStartRename = () => {
    setEditTitle(tree?.topic ?? "");
    setIsEditingTitle(true);
  };

  const handleCancelRename = () => {
    setIsEditingTitle(false);
    setEditTitle("");
  };

  const handleSaveRename = async () => {
    if (!editTitle.trim() || editTitle === tree?.topic) {
      handleCancelRename();
      return;
    }
    try {
      await userApi.renameTopic(topicId, editTitle.trim());
      setTree((prev) => prev ? { ...prev, topic: editTitle.trim() } : prev);
      setIsEditingTitle(false);
    } catch (err) {
      console.error("Failed to rename topic:", err);
    }
  };

  const handleDeleteTopic = async () => {
    setIsDeleting(true);
    try {
      await userApi.deleteTopic(topicId);
      router.push("/profile");
    } catch (err) {
      console.error("Failed to delete topic:", err);
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

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
      {/* Dot-grid background pattern */}
      <div className="pointer-events-none fixed inset-0 z-0 bg-graph-pattern opacity-20" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-surface via-surface/90 to-surface" />

      <Header />

      <div className="relative flex flex-1 overflow-hidden pt-16 z-10">
        {/* Sidebar */}
        <nav className="fixed left-0 top-16 z-40 hidden h-[calc(100vh-64px)] w-64 flex-col border-r border-white/10 bg-surface/70 py-6 text-label-caps backdrop-blur-xl md:flex">
          <div className="mb-8 flex flex-col gap-2 px-6">
            <div className="mb-2 flex h-12 w-12 items-center justify-center rounded bg-primary-container/20 text-primary">
              <Workflow size={24} />
            </div>
            {isEditingTitle ? (
              <div className="flex flex-col gap-2">
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSaveRename();
                    if (e.key === "Escape") handleCancelRename();
                  }}
                  className="w-full rounded border border-white/20 bg-surface-container px-2 py-1.5 text-sm text-on-surface focus:border-primary focus:outline-none"
                  autoFocus
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveRename}
                    className="flex flex-1 items-center justify-center gap-1 rounded bg-tertiary/20 px-2 py-1 text-xs text-tertiary hover:bg-tertiary/30"
                  >
                    <Check size={14} />
                    Save
                  </button>
                  <button
                    onClick={handleCancelRename}
                    className="flex flex-1 items-center justify-center gap-1 rounded bg-white/5 px-2 py-1 text-xs text-on-surface-variant hover:bg-white/10"
                  >
                    <X size={14} />
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="group flex items-center gap-2">
                <h2
                  className="flex-1 truncate text-xl font-semibold text-on-surface"
                  title={tree?.topic ?? "Mastery Hub"}
                >
                  {tree?.topic ?? "Mastery Hub"}
                </h2>
                <button
                  onClick={handleStartRename}
                  className="rounded p-1 text-on-surface-variant opacity-0 transition-opacity hover:bg-white/10 group-hover:opacity-100"
                  title="Rename topic"
                >
                  <Pencil size={14} />
                </button>
              </div>
            )}
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
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex w-full items-center gap-4 px-6 py-3 text-on-surface-variant transition-colors hover:bg-error/10 hover:text-error"
              >
                <Trash2 size={20} />
                Delete Topic
              </button>
            </li>
          </ul>

          {/* Progress card in sidebar */}
          <div className="mt-auto px-6">
            <div className="glass-panel rounded-xl p-4">
              <div className="mb-3 flex items-end gap-2">
                <span className="text-2xl font-bold text-tertiary">{percentComplete}%</span>
                <span className="pb-0.5 text-stats-mono text-on-surface-variant">Complete</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-high">
                <div
                  className="h-full rounded-full bg-tertiary transition-all duration-500"
                  style={{ width: `${percentComplete}%` }}
                />
              </div>
            </div>
          </div>
        </nav>

        {/* Delete confirmation modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="mx-4 w-full max-w-md rounded-xl border border-white/10 bg-surface-container p-6 shadow-2xl">
              <h3 className="mb-2 text-lg font-semibold text-on-surface">Delete Topic?</h3>
              <p className="mb-6 text-sm text-on-surface-variant">
                This will permanently delete &quot;{tree?.topic}&quot; and all associated data including documents, nodes, and progress. This action cannot be undone.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="rounded-lg px-4 py-2 text-sm text-on-surface-variant transition-colors hover:bg-white/10"
                  disabled={isDeleting}
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteTopic}
                  disabled={isDeleting}
                  className="flex items-center gap-2 rounded-lg bg-error px-4 py-2 text-sm font-medium text-on-error transition-colors hover:bg-error/90 disabled:opacity-50"
                >
                  {isDeleting ? "Deleting..." : "Delete Topic"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main panel */}
        <main className="relative flex flex-1 flex-col overflow-hidden md:ml-64">
          {/* Top control bar: Stats + Search + Legend */}
          <div className="glass-panel z-20 border-b border-white/10 px-6 py-3 backdrop-blur-xl">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <StatsStrip
                nodesShown={clusterResult?.displayNodes.length ?? 0}
                nodesUnlocked={nodesUnlocked}
                totalLinks={clusterResult?.displayEdges.length ?? 0}
                knowledgeTiers={numTiers}
                totalNodes={clusterResult?.totalNodeCount ?? 0}
                isFiltered={clusterResult?.isFiltered ?? false}
              />
              <SearchBar
                nodes={allDisplayNodes}
                onSelect={handleSearchSelect}
              />
            </div>

            {/* Legend row */}
            <div className="mt-2 flex flex-wrap items-center gap-5 text-label-caps text-on-surface-variant">
              {[
                { dot: "bg-secondary shadow-[0_0_6px_#4cd7f6]", label: "Foundational" },
                { dot: "bg-tertiary shadow-[0_0_6px_#4edea3]", label: "Intermediate" },
                { dot: "bg-primary shadow-[0_0_6px_#c0c1ff]", label: "Advanced" },
                { dot: "bg-surface-container-high border border-dashed border-white/30", label: "Locked" },
              ].map(({ dot, label }) => (
                <span key={label} className="flex items-center gap-1.5">
                  <span className={`inline-block h-2.5 w-2.5 rounded-full ${dot}`} />
                  {label}
                </span>
              ))}
              <span className="ml-2 text-outline italic">
                Hover = immediate edges · Click = full learning chain
              </span>
            </div>
          </div>

          {/* Canvas area */}
          <div
            className="relative flex-1 overflow-auto"
            style={{ background: "transparent" }}
          >
            <PineCanvas
              nodes={clusterResult?.displayNodes ?? []}
              edges={clusterResult?.displayEdges ?? []}
              layout={layout}
              isFocusing={interaction.isFocusing}
              hoveredId={interaction.hoveredId}
              selectedId={interaction.selectedId}
              litNodeIds={interaction.litNodeIds}
              upstreamEdgeIds={interaction.upstreamEdgeIds}
              downstreamEdgeIds={interaction.downstreamEdgeIds}
              onHoverNode={interaction.onHoverNode}
              onClickNode={handleNodeClick}
              onClickCanvas={interaction.clearSelection}
              scrollToRef={scrollToRef}
            />
          </div>

          {/* Source docs panel (bottom-left, collapsible) */}
          {sourceDocs.length > 0 && (
            <div className="glass-panel absolute bottom-4 left-4 z-20 hidden max-h-64 w-64 flex-col gap-3 overflow-y-auto rounded-xl p-4 text-stats-mono md:flex">
              <h3 className="text-label-caps text-on-surface-variant">Source Docs</h3>
              {sourceDocs.map((source) => (
                <div
                  key={source.doc_id}
                  className="flex items-center gap-2 rounded border border-white/5 bg-surface-container-low p-2 transition-colors hover:border-secondary/40"
                >
                  <FileText size={14} className="shrink-0 text-primary" />
                  <div className="overflow-hidden">
                    <span className="block truncate text-on-surface">{source.title ?? source.doc_id}</span>
                    {source.page != null && (
                      <span className="text-xs text-outline">Page {source.page}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>

      {quizNode && (
        <QuizModal
          nodeLabel={quizNode.title ?? quizNode.name ?? quizNode.id}
          difficultyBadge={quizNode.difficulty_badge}
          xpReward={quizNode.xp_reward}
          estimatedMinutes={quizNode.estimated_minutes}
          quiz={quizNode.quiz}
          lesson={quizNode.lesson}
          sources={quizNode.sources}
          submitting={quizSubmitting}
          result={quizResult}
          error={quizError}
          isGenerating={isGenerating}
          onSubmit={(answers) => submitQuiz(quizNode.id, answers)}
          onClose={closeQuiz}
        />
      )}

      {/* Chat with document panel */}
      <ChatPanel topicId={topicId} topicTitle={tree?.topic} />
    </div>
  );
}

export default function TreePage() {
  return (
    <React.Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-surface p-8">
          <p className="text-on-surface-variant">Loading mastery tree…</p>
        </main>
      }
    >
      <TreePageContent />
    </React.Suspense>
  );
}
