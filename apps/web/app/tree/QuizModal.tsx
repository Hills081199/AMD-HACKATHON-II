"use client";

import { useState } from "react";
import { ArrowRight, CheckCircle2, Lightbulb, Lock, Quote, RotateCcw, Rocket, Sigma, X } from "lucide-react";

import type { NodeLesson, Quiz } from "./types";

export interface QuizResult {
  passed: boolean;
  score: number;
  correct: number;
  total: number;
}

interface QuizModalProps {
  nodeLabel: string;
  quiz?: Quiz | null;
  lesson?: NodeLesson;
  submitting: boolean;
  result: QuizResult | null;
  error: string | null;
  onSubmit: (answers: Record<string, number>) => void;
  onClose: () => void;
}

/** Node detail panel — lesson + real-world example (feat-007) and the
 * checkpoint quiz (feat-008), matching
 * stitch_atlas_learning_path_graph/atlas_learning_derivatives. Submits
 * answers to POST /trees/{topic_id}/nodes/{node_id}/submit-quiz; on a
 * passing result the caller (page.tsx) marks the node completed in
 * progressStore, which re-derives unlock status for its children via
 * feat-006's unlock.ts. */
export function QuizModal({ nodeLabel, quiz, lesson, submitting, result, error, onSubmit, onClose }: QuizModalProps) {
  const [answers, setAnswers] = useState<Record<string, number>>({});

  const allAnswered = quiz?.questions ? quiz.questions.every((question) => answers[question.id] !== undefined) : false;
  const answeredCount = Object.keys(answers).length;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-end bg-background/80 p-4 backdrop-blur-sm md:justify-center md:p-8"
      onClick={onClose}
    >
      <article
        className="glass-panel glow-active relative flex h-[calc(100vh-2rem)] w-full max-w-2xl flex-col overflow-hidden rounded-xl border border-white/10 shadow-2xl md:h-[85vh]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="absolute bottom-0 left-0 top-0 w-1 bg-gradient-to-b from-primary/50 via-secondary/50 to-transparent opacity-50" />

        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-white/10 bg-surface-container/50 p-6 backdrop-blur-md">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-primary/30 bg-primary-container/20">
              <Sigma size={20} className="text-primary" />
            </div>
            <div>
              <p className="mb-1 text-label-caps uppercase tracking-widest text-secondary">Node Unlocked</p>
              <h1 className="m-0 text-headline-lg-mobile leading-tight text-on-surface">{nodeLabel}</h1>
            </div>
          </div>
          <button
            aria-label="Close panel"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-white/10"
          >
            <X size={20} />
          </button>
        </header>

        <div className="flex-1 space-y-8 overflow-y-auto p-6">
          {lesson?.summary && (
            <section className="space-y-4">
              <h2 className="flex items-center gap-2 text-label-caps uppercase tracking-wider text-on-surface-variant">
                <Lightbulb size={18} />
                Quick Lesson
              </h2>
              <div className="relative overflow-hidden rounded-lg border border-white/5 bg-surface-container-low p-5">
                <div className="pointer-events-none absolute -right-16 -top-16 h-32 w-32 rounded-full bg-primary/10 blur-3xl" />
                <p className="relative z-10 leading-relaxed text-on-surface/90">{lesson.summary}</p>
              </div>
            </section>
          )}

          {lesson?.real_world_example && (
            <section className="space-y-4">
              <h2 className="flex items-center gap-2 text-label-caps uppercase tracking-wider text-on-surface-variant">
                <Rocket size={18} />
                Real-world Example
              </h2>
              <div className="flex items-start gap-3 rounded-lg border border-white/5 bg-surface-container-low p-5">
                <Quote size={18} className="mt-1 shrink-0 text-secondary" />
                <p className="text-sm leading-relaxed text-on-surface-variant">{lesson.real_world_example}</p>
              </div>
            </section>
          )}

          <section className="space-y-4 pb-8">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-label-caps uppercase tracking-wider text-on-surface-variant">
                <CheckCircle2 size={18} />
                Checkpoint Quiz
              </h2>
              {quiz?.questions && (
                <span className="text-xs text-outline">
                  {answeredCount}/{quiz.questions.length} Answered
                </span>
              )}
            </div>
            
            {!quiz?.questions || quiz.questions.length === 0 ? (
              <div className="rounded-lg border border-white/5 bg-surface-container-low p-5 text-center">
                <p className="text-on-surface-variant">No quiz available for this node yet.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {quiz.questions.map((question, questionIndex) => (
                  <div
                    key={question.id}
                    className="rounded-lg border border-white/5 bg-surface-container-low p-5 transition-all hover:border-white/10"
                  >
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
        </div>

        <footer className="relative z-10 mt-auto flex flex-col items-center justify-between gap-4 border-t border-white/10 bg-surface/90 p-6 backdrop-blur-md sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-on-surface-variant">
            {result?.passed ? (
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
            disabled={!allAnswered || submitting || result?.passed}
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
