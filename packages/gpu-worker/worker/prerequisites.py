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
                "FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p1-8b-instruct"
            )
        self.timeout = timeout

    def infer_direction(
        self, 
        concept_a: dict, 
        concept_b: dict,
        all_concepts: list[dict] | None = None,
        domain: str = "general learning",
    ) -> dict:
        """Ask whether concept_a or concept_b is a prerequisite of the
        other. Returns {"direction": "a_before_b"|"b_before_a"|"none",
        "confidence": float}."""
        import httpx
        
        context_block = ""
        if all_concepts:
            concept_list = ", ".join(c["name"] for c in all_concepts[:30])
            context_block = (
                f"These two concepts come from a {domain} curriculum that also covers: "
                f"{concept_list}.\n\n"
            )

        prompt = (
            context_block +
            "Determine whether one of these two concepts is a learning prerequisite for the other. "
            "A prerequisite is something a learner must understand BEFORE they can understand the other concept.\n\n"
            f"Concept A: {concept_a['name']} — {concept_a['definition']}\n"
            f"Concept B: {concept_b['name']} — {concept_b['definition']}\n\n"
            'Return strict JSON: {"direction": "a_before_b" | "b_before_a" | "none", '
            '"confidence": <0.0-1.0>, "reasoning": "<one sentence>"}. '
            '"none" means they can be learned independently or in either order.'
        )
        
        for attempt in range(3):
            try:
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
                result = json.loads(content)
                if result.get("direction") in ("a_before_b", "b_before_a", "none"):
                    return result
            except (json.JSONDecodeError, KeyError, httpx.HTTPError) as exc:
                if attempt == 2:
                    print(f"[WARN] infer_direction failed after 3 attempts for "
                          f"({concept_a.get('name')}, {concept_b.get('name')}): {exc}")
                    return {"direction": "none", "confidence": 0.0}
        return {"direction": "none", "confidence": 0.0}


def pre_filter_pairs(concepts: list[dict], similarity_threshold: float = 0.35) -> list[tuple[int, int]]:
    """
    Multi-strategy pre-filter. Includes a pair if it passes ANY of the criteria:
    
    1. High semantic similarity (same as before, but with adaptive threshold)
    2. Name-length disparity heuristic: short-name concepts are often prerequisites of
       longer-name concepts in the same domain (e.g., "Matrix" before "Matrix Decomposition")
    3. Definition containment: if concept A's name appears in concept B's definition, 
       A is likely a prerequisite of B
    """
    if len(concepts) < 2:
        return []

    pairs = set()
    n = len(concepts)
    
    # Strategy 1: Semantic similarity (existing approach)
    vectors = np.asarray([concept["embedding"] for concept in concepts], dtype=float)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit_vectors = vectors / norms
    similarity = unit_vectors @ unit_vectors.T
    
    for i in range(n):
        for j in range(i + 1, n):
            if similarity[i, j] >= similarity_threshold:
                pairs.add((i, j))
    
    # Strategy 2: Name-length disparity
    for i in range(n):
        for j in range(i + 1, n):
            len_i, len_j = len(concepts[i]["name"]), len(concepts[j]["name"])
            ratio = max(len_i, len_j) / max(min(len_i, len_j), 1)
            if ratio >= 2.5 and similarity[i, j] >= 0.2:
                pairs.add((i, j))
    
    # Strategy 3: Definition containment
    for i in range(n):
        for j in range(i + 1, n):
            name_i_lower = concepts[i]["name"].lower()
            name_j_lower = concepts[j]["name"].lower()
            def_i_lower = concepts[i].get("definition", "").lower()
            def_j_lower = concepts[j].get("definition", "").lower()
            if name_i_lower in def_j_lower or name_j_lower in def_i_lower:
                pairs.add((i, j))
    
    return sorted(list(pairs))


MIN_CONFIDENCE = float(os.environ.get("PREREQ_MIN_CONFIDENCE", "0.6"))

def build_candidate_edges(
    concepts: list[dict], 
    fireworks: FireworksClient, 
    similarity_threshold: float = 0.35,
    min_confidence: float = MIN_CONFIDENCE,
) -> list[dict]:
    """Infer directed prerequisite edges (with confidence) for pre-filtered
    concept pairs only. Returns candidate_edges[] as {from, to, confidence}
    dicts keyed by concept id."""
    edges: list[dict] = []
    for i, j in pre_filter_pairs(concepts, similarity_threshold):
        concept_a, concept_b = concepts[i], concepts[j]
        result = fireworks.infer_direction(concept_a, concept_b, all_concepts=concepts)
        direction = result.get("direction")
        confidence = float(result.get("confidence", 0.0))
        
        if confidence < min_confidence:
            continue
            
        if direction == "a_before_b":
            edges.append({"from": concept_a["id"], "to": concept_b["id"], "confidence": confidence})
        elif direction == "b_before_a":
            edges.append({"from": concept_b["id"], "to": concept_a["id"], "confidence": confidence})
    return edges
