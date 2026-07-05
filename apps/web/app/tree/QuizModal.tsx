"use client";

import { useState } from "react";

import type { Quiz } from "./types";

export interface QuizResult {
  passed: boolean;
  score: number;
  correct: number;
  total: number;
}

interface QuizModalProps {
  nodeLabel: string;
  quiz: Quiz;
  submitting: boolean;
  result: QuizResult | null;
  error: string | null;
  onSubmit: (answers: Record<string, number>) => void;
  onClose: () => void;
}

/** Checkpoint quiz UI for feat-008 — submits answers to
 * POST /trees/{topic_id}/nodes/{node_id}/submit-quiz. On a passing result,
 * the caller (page.tsx) marks the node completed in progressStore, which
 * re-derives unlock status for its children via feat-006's unlock.ts. */
export function QuizModal({ nodeLabel, quiz, submitting, result, error, onSubmit, onClose }: QuizModalProps) {
  const [answers, setAnswers] = useState<Record<string, number>>({});

  const allAnswered = quiz.questions.every((question) => answers[question.id] !== undefined);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-4 text-lg font-semibold text-neutral-900">Checkpoint quiz: {nodeLabel}</h2>

        {quiz.questions.map((question) => (
          <fieldset key={question.id} className="mb-4">
            <legend className="mb-2 text-sm font-medium text-neutral-800">{question.question}</legend>
            <div className="space-y-1">
              {question.options.map((option, index) => (
                <label key={index} className="flex items-center gap-2 text-sm text-neutral-700">
                  <input
                    type="radio"
                    name={question.id}
                    checked={answers[question.id] === index}
                    onChange={() => setAnswers((prev) => ({ ...prev, [question.id]: index }))}
                  />
                  {option}
                </label>
              ))}
            </div>
          </fieldset>
        ))}

        {error && <p className="mb-4 text-sm font-medium text-red-600">{error}</p>}

        {result && (
          <p className={`mb-4 text-sm font-medium ${result.passed ? "text-completed" : "text-red-600"}`}>
            {result.passed
              ? `Passed! (${result.correct}/${result.total} correct)`
              : `Not quite — ${result.correct}/${result.total} correct. Try again.`}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            className="rounded px-3 py-1.5 text-sm text-neutral-500 hover:bg-neutral-100"
            onClick={onClose}
          >
            Close
          </button>
          <button
            type="button"
            className="rounded bg-unlocked px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
            disabled={!allAnswered || submitting}
            onClick={() => onSubmit(answers)}
          >
            {submitting ? "Submitting…" : "Submit"}
          </button>
        </div>
      </div>
    </div>
  );
}
