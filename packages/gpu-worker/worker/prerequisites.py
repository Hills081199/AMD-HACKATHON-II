"""Pipeline step 4 — infer prerequisite edges between concepts.

See docs/concept-graph-pipeline.md step 4. Runs here (gpu-worker), not in
apps/api — see docs/architecture.md's "Data contract" section: gpu-worker
produces the candidate graph (nodes + inferred prerequisite edges) and hands
it to api, which starts at the self-checking validation loop (step 5).

IMP-A2: pre_filter_pairs() runs all-pairs for datasets with ≤ MAX_ALL_PAIRS
concepts (default 60) instead of applying a similarity threshold, avoiding
missed prerequisite relationships between semantically dissimilar concepts
(e.g. "Recursion" → "Algorithm Design" may have low cosine similarity but a
clear pedagogical dependency).

IMP-A3: infer_direction() prompt now includes both concepts' difficulty levels,
giving the LLM a strong prior: foundational → advanced edges are much more
likely than the reverse.
"""

from __future__ import annotations

import json
import os

import numpy as np

# IMP-A2: when n ≤ this, skip similarity filter and check all pairs
_MAX_ALL_PAIRS = int(os.environ.get("PREREQ_MAX_ALL_PAIRS", "15"))


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

    def infer_direction(
        self,
        concept_a: dict,
        concept_b: dict,
        all_concepts: list[dict] | None = None,
        domain: str = "general learning",
    ) -> dict:
        """Ask whether concept_a or concept_b is a prerequisite of the
        other. Returns {"direction": "a_before_b"|"b_before_a"|"none",
        "confidence": float}.

        IMP-A3: prompt now includes difficulty levels for both concepts,
        giving the model a strong prior that foundational → intermediate →
        advanced is the natural direction.
        """
        import httpx

        context_block = ""
        if all_concepts:
            concept_list = ", ".join(c["name"] for c in all_concepts[:30])
            context_block = (
                f"These two concepts come from a {domain} curriculum that also covers: "
                f"{concept_list}.\n\n"
            )

        # IMP-A3: include difficulty in the prompt to help the LLM decide direction
        diff_a = concept_a.get("difficulty", "intermediate")
        diff_b = concept_b.get("difficulty", "intermediate")
        difficulty_hint = ""
        if diff_a != diff_b:
            difficulty_hint = (
                f"\nNote: Concept A is marked '{diff_a}' and Concept B is marked '{diff_b}'. "
                "A more foundational concept is typically a prerequisite of a more advanced one. "
                "Use this as a strong prior when the pedagogical relationship is ambiguous.\n"
            )

        prompt = (
            context_block
            + "Determine whether one of these two concepts is a learning prerequisite for the other. "
            "A prerequisite is something a learner must understand BEFORE they can understand the other concept.\n\n"
            f"Concept A: {concept_a['name']} [{diff_a}] — {concept_a['definition']}\n"
            f"Concept B: {concept_b['name']} [{diff_b}] — {concept_b['definition']}\n"
            + difficulty_hint
            + "\nReturn strict JSON only — no prose, no markdown, no code fences: {\"direction\": \"a_before_b\" | \"b_before_a\" | \"none\", "
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
                
                result = json.loads(content)
                if result.get("direction") in ("a_before_b", "b_before_a", "none"):
                    return result
            except (json.JSONDecodeError, KeyError, Exception) as exc:
                if attempt == 2:
                    print(f"[WARN] infer_direction failed after 3 attempts for "
                          f"({concept_a.get('name')}, {concept_b.get('name')}): {exc}")
                    return {"direction": "none", "confidence": 0.0}
        return {"direction": "none", "confidence": 0.0}


def pre_filter_pairs(
    concepts: list[dict],
    similarity_threshold: float = 0.35,
    max_all_pairs: int = _MAX_ALL_PAIRS,
) -> list[tuple[int, int]]:
    """Multi-strategy pre-filter. Returns pairs (i, j) that should be checked
    by the LLM for prerequisite direction.

    IMP-A2: when len(concepts) <= max_all_pairs, ALL pairs are returned
    (no similarity filter). This is the most impactful improvement for small
    datasets (≤60 concepts) — with only 26 concepts we have 325 pairs,
    which is cheap enough to check all of them and avoids missing
    prerequisite relationships between semantically dissimilar concepts
    (e.g. "Recursion" → "Algorithm Design").

    For larger datasets, three complementary strategies are used:
    1. High semantic similarity (cosine ≥ threshold)
    2. Name-length disparity heuristic: short → long often means general → specific
    3. Definition containment: if A's name appears in B's definition, A is likely a prerequisite

    IMP-A3 bonus: difficulty-based pairs are always included when difficulties differ
    (foundational paired with advanced is a very strong prerequisite signal).
    """
    if len(concepts) < 2:
        return []

    n = len(concepts)

    # IMP-A2: small dataset → all pairs, skip similarity filter
    if n <= max_all_pairs:
        return [(i, j) for i in range(n) for j in range(i + 1, n)]

    pairs: set[tuple[int, int]] = set()

    # Strategy 1: Semantic similarity
    vectors = np.asarray([concept["embedding"] for concept in concepts], dtype=float)
    print("concepts: ",concepts)
    print("vectors: ",vectors)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    print("norms: ",norms)
    norms[norms == 0] = 1.0
    unit_vectors = vectors / norms
    similarity = unit_vectors @ unit_vectors.T
    print("similarity: ",similarity)

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

    # IMP-A3 bonus: always include pairs where difficulties differ
    # (foundational ↔ advanced is almost always a prerequisite relationship)
    _DIFF_ORDER = {"foundational": 0, "intermediate": 1, "advanced": 2}
    for i in range(n):
        for j in range(i + 1, n):
            d_i = _DIFF_ORDER.get(concepts[i].get("difficulty", "intermediate"), 1)
            d_j = _DIFF_ORDER.get(concepts[j].get("difficulty", "intermediate"), 1)
            if abs(d_i - d_j) >= 2:  # foundational ↔ advanced
                pairs.add((i, j))

    return sorted(list(pairs))


MIN_CONFIDENCE = float(os.environ.get("PREREQ_MIN_CONFIDENCE", "0.5"))  # IMP-A3: lowered from 0.6


def build_candidate_edges(
    concepts: list[dict],
    fireworks: FireworksClient,
    similarity_threshold: float = 0.35,
    min_confidence: float = MIN_CONFIDENCE,
) -> list[dict]:
    """Infer directed prerequisite edges (with confidence) for pre-filtered
    concept pairs only. Returns candidate_edges[] as {from, to, confidence}
    dicts keyed by concept id.

    IMP-A2: pre_filter_pairs() now uses all-pairs for small datasets.
    IMP-A3: min_confidence lowered to 0.5 (from 0.6) to reduce false negatives.
    """
    import concurrent.futures
    import os

    edges: list[dict] = []
    pairs = pre_filter_pairs(concepts, similarity_threshold)
    print(f"  [Step 4] Checking {len(pairs)} candidate pairs from {len(concepts)} concepts...")

    def _check_pair(pair: tuple[int, int]) -> tuple[dict, dict, str, float]:
        i, j = pair
        concept_a, concept_b = concepts[i], concepts[j]
        result = fireworks.infer_direction(concept_a, concept_b, all_concepts=concepts)
        print(f"  [Step 4] Checking {concept_a.get('name')} -> {concept_b.get('name')}: {result}")
        direction = result.get("direction")
        confidence = float(result.get("confidence", 0.0))
        return concept_a, concept_b, direction, confidence

    max_workers = int(os.environ.get("PREREQ_MAX_WORKERS", "30"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for concept_a, concept_b, direction, confidence in executor.map(_check_pair, pairs):
            if confidence < min_confidence:
                continue

            if direction == "a_before_b":
                edges.append({"from": concept_a["id"], "to": concept_b["id"], "confidence": confidence})
            elif direction == "b_before_a":
                edges.append({"from": concept_b["id"], "to": concept_a["id"], "confidence": confidence})
    return edges
