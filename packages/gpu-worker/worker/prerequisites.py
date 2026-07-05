"""Pipeline step 4 — infer prerequisite edges between concepts.

See docs/concept-graph-pipeline.md step 4. Runs here (gpu-worker), not in
apps/api — see docs/architecture.md's "Data contract" section: gpu-worker
produces the candidate graph (nodes + inferred prerequisite edges) and hands
it to api, which starts at the self-checking validation loop (step 5).
"""

from __future__ import annotations

import json
import os

import numpy as np


class FireworksClient:
    """Client for Fireworks AI's hosted, OpenAI-compatible chat completions
    API. A hosted call is fine here — unlike Gemma concept extraction (step
    2), prerequisite-inference reasoning isn't part of the AMD-platform-usage
    or Best-of-Gemma judging story (see docs/brd.md §4.3, §7.3)."""

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

    def infer_direction(self, concept_a: dict, concept_b: dict) -> dict:
        """Ask whether concept_a or concept_b is a prerequisite of the
        other. Returns {"direction": "a_before_b"|"b_before_a"|"none",
        "confidence": float}."""
        import httpx

        prompt = (
            "Determine whether one of these two concepts is a learning "
            "prerequisite for the other.\n"
            f"Concept A: {concept_a['name']} — {concept_a['definition']}\n"
            f"Concept B: {concept_b['name']} — {concept_b['definition']}\n\n"
            'Return strict JSON: {"direction": "a_before_b" | "b_before_a" '
            '| "none", "confidence": <0.0-1.0>}. "a_before_b" means a '
            'learner must understand Concept A before Concept B. "none" '
            "means neither is a prerequisite of the other."
        )
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


def pre_filter_pairs(concepts: list[dict], similarity_threshold: float = 0.35) -> list[tuple[int, int]]:
    """Pre-filter candidate concept pairs by embedding similarity so step 4
    only calls Fireworks on plausible pairs instead of scanning all O(n^2)
    combinations — see docs/concept-graph-pipeline.md's cost-avoidance note."""
    if len(concepts) < 2:
        return []

    vectors = np.asarray([concept["embedding"] for concept in concepts], dtype=float)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit_vectors = vectors / norms
    similarity = unit_vectors @ unit_vectors.T

    pairs: list[tuple[int, int]] = []
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            if similarity[i, j] >= similarity_threshold:
                pairs.append((i, j))
    return pairs


def build_candidate_edges(
    concepts: list[dict], fireworks: FireworksClient, similarity_threshold: float = 0.35
) -> list[dict]:
    """Infer directed prerequisite edges (with confidence) for pre-filtered
    concept pairs only. Returns candidate_edges[] as {from, to, confidence}
    dicts keyed by concept id."""
    edges: list[dict] = []
    for i, j in pre_filter_pairs(concepts, similarity_threshold):
        concept_a, concept_b = concepts[i], concepts[j]
        result = fireworks.infer_direction(concept_a, concept_b)
        direction = result.get("direction")
        confidence = float(result.get("confidence", 0.0))
        if direction == "a_before_b":
            edges.append({"from": concept_a["id"], "to": concept_b["id"], "confidence": confidence})
        elif direction == "b_before_a":
            edges.append({"from": concept_b["id"], "to": concept_a["id"], "confidence": confidence})
    return edges
