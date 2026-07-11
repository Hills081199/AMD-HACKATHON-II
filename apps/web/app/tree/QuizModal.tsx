"use client";

import { useState } from "react";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  FileText,
  Lightbulb,
  Loader2,
  Lock,
  Quote,
  RotateCcw,
  Rocket,
  Sigma,
  Sparkles,
  Star,
  X,
  Zap,
} from "lucide-react";

import type { NodeLesson, NodeSource, Quiz } from "./types";

export interface QuizResult {
  passed: boolean;
  score: number;
  correct: number;
  total: number;
}

interface QuizModalProps {
  nodeLabel: string;
  difficultyBadge?: string;
  xpReward?: number;
  estimatedMinutes?: number;
  quiz?: Quiz | null;
  lesson?: NodeLesson;
  sources?: NodeSource[];
  submitting: boolean;
  result: QuizResult | null;
  error: string | null;
  isGenerating?: boolean;
  onSubmit: (answers: Record<string, number>) => void;
  onClose: () => void;
}

/** Node detail panel — lesson + real-world example (feat-007) and the
 * checkpoint quiz (feat-008). Now shows full node metadata including
 * difficulty badge, XP reward, estimated time, and sources. Supports
 * on-demand lesson/quiz generation with a loading state. */
export function QuizModal({
  nodeLabel,
  difficultyBadge,
  xpReward,
  estimatedMinutes,
  quiz,
  lesson,
  sources,
  submitting,
  result,
  error,
  isGenerating = false,
  onSubmit,
  onClose,
}: QuizModalProps) {
  const [answers, setAnswers] = useState<Record<string, number>>({});

  const allAnswered = quiz?.questions
    ? quiz.questions.every((question) => answers[question.id] !== undefined)
    : false;
  const answeredCount = Object.keys(answers).length;

  const hasLesson = lesson?.summary && lesson.summary.trim().length > 0;
  const hasExample = lesson?.real_world_example && lesson.real_world_example.trim().length > 0;
  const hasQuiz = quiz?.questions && quiz.questions.length > 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-end bg-background/80 p-4 backdrop-blur-sm md:justify-center md:p-8"
      onClick={onClose}
    >
      <article
        className="glass-panel glow-active relative flex h-[calc(100vh-2rem)] w-full max-w-2xl flex-col overflow-hidden rounded-xl border border-white/10 shadow-2xl md:h-[90vh]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="absolute bottom-0 left-0 top-0 w-1 bg-gradient-to-b from-primary/50 via-secondary/50 to-transparent opacity-50" />

        {/* Header */}
        <header className="sticky top-0 z-10 flex items-start justify-between border-b border-white/10 bg-surface-container/50 p-6 backdrop-blur-md">
          <div className="flex items-start gap-4 flex-1 min-w-0">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-primary/30 bg-primary-container/20">
              <Sigma size={20} className="text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="mb-1 text-label-caps uppercase tracking-widest text-secondary">Node Unlocked</p>
              <h1 className="m-0 text-headline-lg-mobile leading-tight text-on-surface break-words">{nodeLabel}</h1>

              {/* Metadata badges */}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {difficultyBadge && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-surface-container-high px-2.5 py-0.5 text-xs text-on-surface-variant">
                    {difficultyBadge}
                  </span>
                )}
                {xpReward != null && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-tertiary/30 bg-tertiary/10 px-2.5 py-0.5 text-xs text-tertiary">
                    <Zap size={11} />
                    {xpReward} XP
                  </span>
                )}
                {estimatedMinutes != null && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-surface-container-high px-2.5 py-0.5 text-xs text-on-surface-variant">
                    <Clock size={11} />
                    {estimatedMinutes} min
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            aria-label="Close panel"
            onClick={onClose}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-white/10"
          >
            <X size={20} />
          </button>
        </header>

        {/* Body */}
        <div className="flex-1 space-y-8 overflow-y-auto p-6">

          {/* ── LOADING STATE ── */}
          {isGenerating && (
            <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-primary/20 bg-primary-container/10 px-6 py-10">
              <div className="relative flex items-center justify-center">
                <div className="absolute h-16 w-16 rounded-full border border-primary/30 animate-ping opacity-30" />
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20 border border-primary/40">
                  <Sparkles size={22} className="text-primary animate-pulse" />
                </div>
              </div>
              <div className="text-center">
                <p className="font-semibold text-on-surface">Đang tạo bài học với AI…</p>
                <p className="mt-1 text-sm text-on-surface-variant">
                  Fireworks AI đang phân tích tài liệu và sinh lesson + quiz cho node này.
                </p>
                <div className="mt-3 flex items-center justify-center gap-2 text-xs text-outline">
                  <Loader2 size={13} className="animate-spin" />
                  Có thể mất 10–30 giây
                </div>
              </div>
            </div>
          )}

          {/* ── LESSON ── */}
          {!isGenerating && hasLesson && (
            <section className="space-y-4">
              <h2 className="flex items-center gap-2 text-label-caps uppercase tracking-wider text-on-surface-variant">
                <Lightbulb size={18} />
                Quick Lesson
              </h2>
              <div className="relative overflow-hidden rounded-lg border border-white/5 bg-surface-container-low p-5">
                <div className="pointer-events-none absolute -right-16 -top-16 h-32 w-32 rounded-full bg-primary/10 blur-3xl" />
                <p className="relative z-10 leading-relaxed text-on-surface/90">{lesson!.summary}</p>
              </div>
            </section>
          )}

          {/* ── REAL-WORLD EXAMPLE ── */}
          {!isGenerating && hasExample && (
            <section className="space-y-4">
              <h2 className="flex items-center gap-2 text-label-caps uppercase tracking-wider text-on-surface-variant">
                <Rocket size={18} />
                Real-world Example
              </h2>
              <div className="flex items-start gap-3 rounded-lg border border-white/5 bg-surface-container-low p-5">
                <Quote size={18} className="mt-1 shrink-0 text-secondary" />
                <p className="text-sm leading-relaxed text-on-surface-variant">{lesson!.real_world_example}</p>
              </div>
            </section>
          )}

          {/* ── PLACEHOLDER when no lesson yet and not generating ── */}
          {!isGenerating && !hasLesson && (
            <div className="rounded-lg border border-dashed border-white/10 bg-surface-container-low p-6 text-center">
              <BookOpen size={28} className="mx-auto mb-3 text-outline" />
              <p className="text-sm text-on-surface-variant">Chưa có bài học. Hệ thống sẽ tự sinh nội dung khi bạn mở node này.</p>
            </div>
          )}

          {/* ── CHECKPOINT QUIZ ── */}
          <section className="space-y-4 pb-8">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-label-caps uppercase tracking-wider text-on-surface-variant">
                <CheckCircle2 size={18} />
                Checkpoint Quiz
              </h2>
              {!isGenerating && hasQuiz && (
                <span className="text-xs text-outline">
                  {answeredCount}/{quiz!.questions.length} Answered
                </span>
              )}
            </div>

            {isGenerating ? (
              /* Quiz loading skeleton */
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="rounded-lg border border-white/5 bg-surface-container-low p-5 animate-pulse">
                    <div className="mb-4 h-3 w-3/4 rounded bg-white/10" />
                    <div className="space-y-2">
                      {[1, 2, 3, 4].map((j) => (
                        <div key={j} className="h-10 rounded-md bg-white/5" />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : !hasQuiz ? (
              <div className="rounded-lg border border-white/5 bg-surface-container-low p-5 text-center">
                <p className="text-on-surface-variant">No quiz available for this node yet.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {quiz!.questions.map((question, questionIndex) => (
                  <div
                    key={question.id}
                    className="rounded-lg border border-white/5 bg-surface-container-low p-5 transition-all hover:border-white/10"
                  >
                    {question.difficulty && (
                      <span className="mb-2 inline-block rounded bg-white/5 px-2 py-0.5 text-[10px] text-outline capitalize">
                        {question.difficulty}
                      </span>
                    )}
                    <p className="mb-4 font-medium text-on-surface">
                      {questionIndex + 1}. {question.question}
                    </p>
                    <div className="space-y-2">
                      {question.options.map((option, optionIndex) => {
                        const selected = answers[question.id] === optionIndex;
                        return (
                          <label
                            key={optionIndex}
                            className={`group relative flex cursor-pointer items-start gap-3 overflow-hidden rounded-md border p-3 transition-colors ${
                              selected
                                ? "border-secondary/50 bg-secondary/10"
                                : "border-white/5 bg-background/50 hover:bg-white/5"
                            }`}
                          >
                            <input
                              type="radio"
                              name={question.id}
                              checked={selected}
                              onChange={() => setAnswers((prev) => ({ ...prev, [question.id]: optionIndex }))}
                              className="mt-1 border-outline-variant bg-surface text-secondary focus:ring-secondary focus:ring-offset-background"
                            />
                            <span
                              className={`relative z-10 text-sm ${selected ? "font-medium text-on-surface" : "text-on-surface-variant group-hover:text-on-surface"}`}
                            >
                              {option}
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {error && <p className="text-sm font-medium text-error">{error}</p>}

            {result && (
              <p className={`text-sm font-medium ${result.passed ? "text-tertiary" : "text-error"}`}>
                {result.passed
                  ? `Passed! (${result.correct}/${result.total} correct)`
                  : `Not quite — ${result.correct}/${result.total} correct. Try again.`}
              </p>
            )}
          </section>

          {/* ── SOURCES ── */}
          {!isGenerating && sources && sources.length > 0 && (
            <section className="space-y-3 pb-4">
              <h2 className="flex items-center gap-2 text-label-caps uppercase tracking-wider text-on-surface-variant">
                <FileText size={16} />
                Source References
              </h2>
              <div className="flex flex-wrap gap-2">
                {sources.map((src, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-surface-container-high px-3 py-1.5 text-xs text-on-surface-variant"
                  >
                    <FileText size={11} className="shrink-0 text-primary" />
                    <span className="truncate max-w-[160px]" title={src.doc_id}>{src.doc_id}</span>
                    {src.page != null && (
                      <span className="text-outline">p.{src.page}</span>
                    )}
                  </span>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <footer className="relative z-10 mt-auto flex flex-col items-center justify-between gap-4 border-t border-white/10 bg-surface/90 p-6 backdrop-blur-md sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-on-surface-variant">
            {isGenerating ? (
              <>
                <Loader2 size={18} className="animate-spin text-primary" />
                <span>Đang sinh nội dung…</span>
              </>
            ) : result?.passed ? (
              <>
                <CheckCircle2 size={18} className="text-tertiary" />
                <span>Node completed</span>
              </>
            ) : result ? (
              <>
                <RotateCcw size={18} className="text-outline" />
                <span>Try again</span>
              </>
            ) : (
              <>
                <Lock size={18} className="text-outline" />
                <span>Complete quiz to proceed</span>
              </>
            )}
          </div>
          <button
            type="button"
            disabled={!allAnswered || submitting || result?.passed || isGenerating}
            onClick={() => onSubmit(answers)}
            className="group flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-8 py-3 font-medium text-on-primary shadow-[0_0_15px_rgba(192,193,255,0.15)] transition-all duration-200 hover:bg-primary-fixed disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
          >
            {submitting ? "Submitting…" : "Submit Quiz"}
            <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
          </button>
        </footer>
      </article>
    </div>
  );
}
