"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { BookOpen, ChevronDown, ChevronRight, ChevronUp, FileText, Network, Settings2, Workflow } from "lucide-react";
import React from "react";

import { userApi } from "../lib/api";
import type { TopicSummary } from "../lib/types";
import { Header } from "../components/Header";
import { QuizModal, type QuizResult } from "./QuizModal";
import { StatsStrip } from "./StatsStrip";
import { SearchBar } from "./SearchBar";
import { PineCanvas } from "./PineCanvas";
import { usePineInteraction } from "./usePineInteraction";
import { computePineLayout } from "./pineLayout";
import { clusterForDisplay } from "./clusterNodes";
import { useTreeProgressStore } from "./progressStore";
import { deriveNodeStatuses, seedCompletedIds, toDisplayNodes } from "./unlock";
import type { RawTreeNode, TreeResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEFAULT_TOPIC_ID = "intro-to-ml";

function TreePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const topicId = searchParams.get("topic") || DEFAULT_TOPIC_ID;

  const [tree, setTree] = useState<TreeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [userTopics, setUserTopics] = useState<TopicSummary[]>([]);
  const completedIds = useTreeProgressStore((state) => state.completedIds);
  const seedCompleted = useTreeProgressStore((state) => state.seedCompleted);
  const markCompleted = useTreeProgressStore((state) => state.markCompleted);

  const [quizNodeId, setQuizNodeId] = useState<string | null>(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [quizError, setQuizError] = useState<string | null>(null);
  const [navPanelOpen, setNavPanelOpen] = useState(false);

  // State for on-demand lesson/quiz generation
  const [isGenerating, setIsGenerating] = useState(false);

  // Ref that PineCanvas populates so SearchBar can scroll to a node
  const scrollToRef = useRef<((nodeId: string) => void) | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/trees/${topicId}`)
      .then((response) => {
        if (!response.ok) throw new Error(`GET /trees/${topicId} failed: ${response.status}`);
        return response.json() as Promise<TreeResponse>;
      })
      .then((data) => {
        setTree(data);
        seedCompleted(seedCompletedIds(data.nodes));
      })
      .catch((err: Error) => setError(err.message));
  }, [topicId, seedCompleted]);

  // Fetch user's topics for navigation
  useEffect(() => {
    userApi
      .getTopics()
      .then((topics) => setUserTopics(topics.filter((t) => t.status === "completed")))
      .catch(() => {
        // User not logged in or no topics - silently ignore
      });
  }, []);

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

  // Node click: open quiz OR select for chain highlight
  function handleNodeClick(nodeId: string) {
    interaction.onClickNode(nodeId);
    const status = statusById.get(nodeId);
    if (status === "unlocked") {
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
      if (body.passed) markCompleted(nodeId);
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
            <h2
              className="truncate text-xl font-semibold text-on-surface"
              title={tree?.topic ?? "Mastery Hub"}
            >
              {tree?.topic ?? "Mastery Hub"}
            </h2>
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

          {/* Navigation panel - switch between topics (collapsible) */}
          {userTopics.length > 0 && (
            <div className="absolute bottom-4 right-4 z-20 hidden md:block">
              {/* Toggle button when collapsed */}
              {!navPanelOpen && (
                <button
                  onClick={() => setNavPanelOpen(true)}
                  className="glass-panel flex items-center gap-2 rounded-xl px-4 py-3 text-sm text-on-surface-variant transition-colors hover:text-on-surface"
                >
                  <BookOpen size={16} />
                  <span>My Paths ({userTopics.length})</span>
                  <ChevronUp size={16} />
                </button>
              )}

              {/* Expanded panel */}
              {navPanelOpen && (
                <div className="glass-panel max-h-80 w-72 flex-col gap-3 overflow-y-auto rounded-xl p-4 text-stats-mono">
                  <button
                    onClick={() => setNavPanelOpen(false)}
                    className="mb-3 flex w-full items-center justify-between text-label-caps text-on-surface-variant transition-colors hover:text-on-surface"
                  >
                    <span className="flex items-center gap-2">
                      <BookOpen size={16} />
                      My Learning Paths
                    </span>
                    <ChevronDown size={16} />
                  </button>
                  <div className="flex flex-col gap-2">
                    {userTopics.map((topic) => {
                      const isActive = topic.id === topicId;
                      return (
                        <button
                          key={topic.id}
                          onClick={() => router.push(`/tree?topic=${topic.id}`)}
                          className={`group flex items-center justify-between gap-2 rounded-lg border p-3 text-left transition-all ${
                            isActive
                              ? "border-secondary/50 bg-secondary/10"
                              : "border-white/5 bg-surface-container-low hover:border-secondary/30 hover:bg-white/5"
                          }`}
                        >
                          <div className="flex items-center gap-3 overflow-hidden">
                            <div
                              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${
                                isActive ? "bg-secondary/20 text-secondary" : "bg-primary-container/20 text-primary"
                              }`}
                            >
                              <Network size={16} />
                            </div>
                            <div className="overflow-hidden">
                              <span
                                className={`block truncate text-sm font-medium ${
                                  isActive ? "text-secondary" : "text-on-surface"
                                }`}
                              >
                                {topic.title ?? topic.id}
                              </span>
                              <span className="text-xs text-outline">
                                {topic.document_count} doc{topic.document_count !== 1 ? "s" : ""}
                              </span>
                            </div>
                          </div>
                          <ChevronRight
                            size={16}
                            className={`shrink-0 transition-transform ${
                              isActive ? "text-secondary" : "text-outline group-hover:translate-x-0.5"
                            }`}
                          />
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
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
