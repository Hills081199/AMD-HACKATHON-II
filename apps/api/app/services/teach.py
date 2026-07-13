"""Pipeline step 7 — per-node lesson + quiz + real-world example (agentic RAG).

See docs/concept-graph-pipeline.md's "Teach" stage and
docs/hackathon-scope.md §3's "Agentic RAG for lesson & quiz generation" row:
per node, retrieve only that node's own source chunks (never the whole
corpus) and have the agent self-check that the generated quiz actually
matches the generated lesson before returning it, regenerating at least once
if it doesn't.

IMP-B2: generate 3 MCQ questions (easy/medium/hard) instead of 1. The
pass_threshold in the output is now level-aware (higher levels require a
higher score to unlock the next concept).

IMP-B3: lesson prompt now includes the names of prerequisite concepts so the
generated lesson can acknowledge what the learner should already know.

IMP-D1: max_attempts increased from 2 to 3 for the self-check loop.
"""

from __future__ import annotations

import json
import os


class FireworksClient:
    """Client for Fireworks AI's hosted, OpenAI-compatible chat completions
    API, used for lesson/quiz/example generation and the alignment
    self-check. Separate from packages/gpu-worker's FireworksClient (step 4)
    since apps/api and gpu-worker are independently deployable services —
    see docs/architecture.md's Data contract section."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ):
        # LLM_PROVIDER=openai is a prototyping-only switch (see
        # docs/hackathon-scope.md §5) to validate this step against GPT-4o
        # mini before a real Fireworks account is provisioned — safe because
        # Fireworks' API is itself OpenAI-compatible, so no request-shape
        # changes are needed, only which credentials/base_url get used.
        use_openai = os.environ.get("LLM_PROVIDER", "").lower() == "openai"
        if use_openai:
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
            self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
            self.model = model or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
        else:
            self.api_key = api_key or os.environ.get("FIREWORKS_API_KEY", "")
            self.base_url = (
                base_url or os.environ.get("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
            ).rstrip("/")
            self.model = model or os.environ.get(
                "FIREWORKS_MODEL", "accounts/fireworks/models/deepseek-v4-pro"
            )
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> dict:
        """Simple chat completion for conversational use cases."""
        import httpx

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _chat_json(self, prompt: str) -> dict:
        import httpx

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)

    def generate(
        self,
        node_name: str,
        chunks: list[dict],
        prerequisite_names: list[str] | None = None,
        node_level: int = 0,
    ) -> dict:
        """Generate a lesson, 3 MCQ checkpoint questions, and a real-world
        example, grounded only in the given chunks (this node's own
        sources[], never the full corpus).

        IMP-B2: returns 3 questions (easy/medium/hard) instead of 1.
        IMP-B3: prerequisite_names are woven into the lesson prompt so the
        generated lesson can reference what the learner should know first.

        Returns {"lesson": str, "questions": [{...}, ...], "example": str}.
        """
        excerpts = "\n\n".join(f"[{chunk['chunk_id']}] {chunk['text']}" for chunk in chunks)

        # IMP-B3: prerequisite context in lesson prompt
        prereq_block = ""
        if prerequisite_names:
            prereq_list = ", ".join(prerequisite_names)
            prereq_block = (
                f"The learner has already studied: {prereq_list}. "
                "Briefly acknowledge these prerequisites at the start of the lesson "
                "and build on them where relevant.\n\n"
            )

        # IMP-B2: request 3 questions with difficulty grading
        prompt = (
            f"You are teaching the concept \"{node_name}\" using only the "
            f"source excerpts below — do not use outside knowledge.\n\n"
            f"{prereq_block}"
            f"{excerpts}\n\n"
            "Return strict JSON only — no prose, no markdown, no code fences:\n"
            "{\n"
            '  "lesson": "<2-4 sentence explanation>",\n'
            '  "questions": [\n'
            '    {"difficulty": "easy",   "question": "<MCQ question>", "options": ["...", "...", "...", "..."], "answer_index": <int>},\n'
            '    {"difficulty": "medium", "question": "<MCQ question>", "options": ["...", "...", "...", "..."], "answer_index": <int>},\n'
            '    {"difficulty": "hard",   "question": "<MCQ question>", "options": ["...", "...", "...", "..."], "answer_index": <int>}\n'
            "  ],\n"
            '  "example": "<one real-world example>"\n'
            "}"
        )
        return self._chat_json(prompt)

    def check_alignment(self, node_name: str, lesson: str, questions: list[dict]) -> bool:
        """Self-check: do these quiz questions actually test the content of
        this lesson? Returns True if aligned, False if questions should be
        regenerated. See docs/hackathon-scope.md §3's Agentic RAG row.

        IMP-B2: now checks all 3 questions, not just 1.
        """
        q_block = "\n".join(
            f"  [{q.get('difficulty','?')}] {q.get('question')} "
            f"(answer_index={q.get('answer_index')})"
            for q in questions
        )
        prompt = (
            f"Lesson about \"{node_name}\":\n{lesson}\n\n"
            f"Quiz questions:\n{q_block}\n\n"
            "Do ALL of these quiz questions require understanding the lesson above "
            "(not outside knowledge), and are the marked answers actually correct? "
            'Return strict JSON only — no prose, no markdown, no code fences: {"aligned": true|false}.'
        )
        result = self._chat_json(prompt)
        return bool(result.get("aligned", False))


def _level_to_pass_threshold(level: int) -> float:
    """IMP-B2: pass threshold scales with node level.
    Level 0 (foundational) = 60%, Level 1 = 70%, Level 2+ = 80%.
    This makes gatekeeping progressively stricter as the learner advances.
    """
    if level <= 0:
        return 0.6
    if level == 1:
        return 0.7
    return 0.8


def generate_lesson_package(
    node_name: str,
    chunks: list[dict],
    fireworks: FireworksClient,
    prerequisite_names: list[str] | None = None,
    node_level: int = 0,
    max_attempts: int = 3,  # IMP-D1: was 2
) -> dict:
    """Orchestrate step 7: generate a lesson/quiz/example scoped to `chunks`
    only, then self-check that the quiz matches the lesson before returning
    it, regenerating up to `max_attempts` times.

    IMP-B2: returns 3 questions with difficulty grading. pass_threshold is
    now level-aware (level 0 = 60%, level 1 = 70%, level 2+ = 80%).
    IMP-B3: prerequisite_names passed into lesson generation prompt.
    IMP-D1: max_attempts increased from 2 to 3.

    Always returns a result — if every attempt fails the self-check, the
    last attempt is returned with self_check.passed = False so the caller/UI
    can flag it, rather than silently serving an unchecked quiz or raising.
    """
    attempts: list[dict] = []
    package: dict = {}

    for attempt in range(1, max_attempts + 1):
        package = fireworks.generate(
            node_name,
            chunks,
            prerequisite_names=prerequisite_names,
            node_level=node_level,
        )
        questions = package.get("questions", [])
        aligned = fireworks.check_alignment(node_name, package.get("lesson", ""), questions)
        attempts.append({"attempt": attempt, "aligned": aligned})
        if aligned:
            break

    questions = package.get("questions", [])
    # Backward-compatible: also expose the first question as "quiz" for
    # callers that only consume the single-question format.
    first_q = questions[0] if questions else {}

    return {
        "lesson": package.get("lesson", ""),
        "quiz": first_q,          # legacy single-question field
        "questions": questions,   # IMP-B2: full multi-question list
        "example": package.get("example", ""),
        "sources": [
            {"chunk_id": chunk["chunk_id"], "doc_id": chunk["doc_id"], "page": chunk.get("page")}
            for chunk in chunks
        ],
        "self_check": {
            "passed": attempts[-1]["aligned"],
            "attempts": len(attempts),
        },
        "pass_threshold": _level_to_pass_threshold(node_level),  # IMP-B2
    }
