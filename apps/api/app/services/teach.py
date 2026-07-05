"""Pipeline step 7 — per-node lesson + quiz + real-world example (agentic RAG).

See docs/concept-graph-pipeline.md's "Teach" stage and
docs/hackathon-scope.md §3's "Agentic RAG for lesson & quiz generation" row:
per node, retrieve only that node's own source chunks (never the whole
corpus) and have the agent self-check that the generated quiz actually
matches the generated lesson before returning it, regenerating at least once
if it doesn't.
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
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("FIREWORKS_API_KEY", "")
        self.base_url = (
            base_url or os.environ.get("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
        ).rstrip("/")
        self.model = model or os.environ.get(
            "FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p1-8b-instruct"
        )
        self.timeout = timeout

    def _chat_json(self, prompt: str) -> dict:
        import httpx

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    def generate(self, node_name: str, chunks: list[dict]) -> dict:
        """Generate a lesson, an MCQ checkpoint quiz, and a real-world
        example, grounded only in the given chunks (this node's own
        sources[], never the full corpus). Returns
        {"lesson": str, "quiz": {...}, "example": str}."""
        excerpts = "\n\n".join(f"[{chunk['chunk_id']}] {chunk['text']}" for chunk in chunks)
        prompt = (
            f"You are teaching the concept \"{node_name}\" using only the "
            f"source excerpts below — do not use outside knowledge.\n\n{excerpts}\n\n"
            'Return strict JSON: {"lesson": "<2-4 sentence explanation>", '
            '"quiz": {"question": "<one MCQ question>", "options": ["...", "...", "...", "..."], '
            '"answer_index": <int>}, "example": "<one real-world example>"}.'
        )
        return self._chat_json(prompt)

    def check_alignment(self, node_name: str, lesson: str, quiz: dict) -> bool:
        """Self-check: does this quiz actually test the content of this
        lesson? Returns True if aligned, False if the quiz should be
        regenerated. See docs/hackathon-scope.md §3's Agentic RAG row."""
        prompt = (
            f"Lesson about \"{node_name}\":\n{lesson}\n\n"
            f"Quiz question: {quiz.get('question')}\n"
            f"Options: {quiz.get('options')}\n"
            f"Marked correct answer index: {quiz.get('answer_index')}\n\n"
            "Does answering this quiz question correctly require understanding "
            'the lesson above (not outside knowledge), and is the marked answer '
            'actually correct? Return strict JSON: {"aligned": true|false}.'
        )
        result = self._chat_json(prompt)
        return bool(result.get("aligned", False))


def generate_lesson_package(
    node_name: str,
    chunks: list[dict],
    fireworks: FireworksClient,
    max_attempts: int = 2,
) -> dict:
    """Orchestrate step 7: generate a lesson/quiz/example scoped to `chunks`
    only, then self-check that the quiz matches the lesson before returning
    it, regenerating up to `max_attempts` times. Always returns a result —
    if every attempt fails the self-check, the last attempt is returned with
    self_check.passed = False so the caller/UI can flag it, rather than
    silently serving an unchecked quiz or raising."""
    attempts: list[dict] = []
    package: dict = {}

    for attempt in range(1, max_attempts + 1):
        package = fireworks.generate(node_name, chunks)
        aligned = fireworks.check_alignment(node_name, package["lesson"], package["quiz"])
        attempts.append({"attempt": attempt, "aligned": aligned})
        if aligned:
            break

    return {
        "lesson": package["lesson"],
        "quiz": package["quiz"],
        "example": package["example"],
        "sources": [
            {"chunk_id": chunk["chunk_id"], "doc_id": chunk["doc_id"], "page": chunk.get("page")}
            for chunk in chunks
        ],
        "self_check": {
            "passed": attempts[-1]["aligned"],
            "attempts": len(attempts),
        },
    }
