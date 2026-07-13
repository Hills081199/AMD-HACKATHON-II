# Concept graph pipeline — the heart of the system

This is the canonical detail doc for the "Understand" and "Structure" stages
in [`architecture.md`](architecture.md): the 6-step chain that turns a messy
pile of documents into a validated, tiered concept-dependency graph. See
[`hackathon-scope.md`](hackathon-scope.md) for why this pipeline is the core
demo differentiator and how it fits the 7-day build plan.

## Step-by-step detail + tech stack

| # | Step | What happens | Input → Output | Technology |
|---|------|--------------|-----------------|------------|
| 1 | **Chunk & embed** | Parse files (PDF/PPTX/DOCX...), split by heading/slide boundaries (not by a hard character count — that risks cutting a concept in half), then vectorize each chunk | Raw files → `chunks[]` with doc_id, page, embedding | PyMuPDF/unstructured.io (parsing) + sentence-transformers (bge-large/e5-large) running on ROCm-enabled PyTorch |
| 2 | **Extract concepts** | For each chunk, ask an LLM: "which concepts does this chunk mention, and what's their canonical name?" → return structured JSON | `chunks[]` → `raw_concepts[]` (name + short definition + originating chunk_id) | **Gemma** (2B/7B) served locally via vLLM-ROCm or Ollama, on the AMD GPU — qualifies for the "Best Use of Gemma" bonus and is the piece of the pipeline that puts actual LLM inference on AMD hardware (see [`brd.md`](brd.md) §7.3) |
| 3 | **Cluster & dedupe** | Merge concepts that mean the same thing but are phrased differently (e.g. "gradient descent" vs. "the steepest-descent optimization algorithm") into a single canonical node | `raw_concepts[]` → `canonical_concepts[]` | Cosine similarity on embeddings (numpy/faiss) + networkx/igraph Louvain clustering — **no LLM needed** here, saves cost |
| 4 | **Infer prerequisites** | For **pre-filtered pairs of concepts only** (only pairs with high similarity or that co-occur nearby, to avoid O(n²)), ask an LLM: "is A a prerequisite for understanding B?" → return a directed edge with a confidence score | `canonical_concepts[]` (filtered pairs) → `candidate_edges[]` (A→B, confidence) | **Fireworks AI** (Llama 3.x) — hosted reasoning, kept separate from the local Gemma tagging step |
| 5 | **Validate graph (self-checking agent)** | Build a `networkx.DiGraph`, run `nx.simple_cycles()` to detect cycles; if found, the agent drops the lowest-confidence edge in the cycle, repeating up to N iterations (fallback: if a cycle remains after N tries, drop the weakest edge regardless) | `candidate_edges[]` → `valid_dag` | networkx (cycle detection) + plain Python logic for the repair loop + optional re-call to Fireworks to re-evaluate an edge |
| 6 | **Assign levels** | Use `nx.topological_generations()` (not just a single linear order) to group nodes into "tiers" — allowing multiple parallel learning branches, closer to a real skill tree than one straight line | `valid_dag` → `nodes[]` with level, position | networkx — built in, no need to write this from scratch |

## Key design decisions to keep in mind

- **Don't call the LLM for every possible pair of concepts (O(n²)).** With 30 documents you might end up with 100-200 concepts — checking every pair would mean tens of thousands of Fireworks calls, both expensive and slow. Pre-filter using embedding similarity and co-occurrence within nearby chunks, so only a few hundred "plausible" pairs are ever sent to the LLM.
- **Use "levels" (tiers) instead of a single linear order.** A DAG genuinely admits multiple valid orderings — forcing it into one straight line loses the feeling of a skill tree with parallel branches (like a real game). `topological_generations` gives you tiered structure, which is truer to the skill-tree spirit than a plain `topological_sort`.
- **Attach a confidence score to every edge** inferred in step 4 — this is the "fuel" the agent uses to self-repair in step 5 (dropping the weakest edge when a cycle is found), instead of having to call the LLM again every time an error is hit.
- **Carry `chunk_id`/`doc_id`/`page` all the way through, from step 1 to the final node** — this data is required so every node in the mastery tree has sources (citations), which matters both for the Teach stage (agentic RAG) and for credibility in front of judges during the demo.
- **Pre-index the demo dataset ahead of time.** Run this entire 6-step pipeline on the chosen document set beforehand and save the static output, so the live demo doesn't depend on Fireworks' latency or reliability in the moment.

## Node and edge schema (after step 6)

```json
// node
{
  "id": "concept_042",
  "name": "Gradient descent",
  "level": 1,
  "sources": [{"doc_id": "calculus_notes.pdf", "page": 12, "chunk_id": "c88"}],
  "status": "locked" // locked | unlocked | completed
}

// edge
{ "from": "concept_010", "to": "concept_042", "confidence": 0.87 }
```

The frontend (React Flow) only needs to read `nodes[]` + `edges[]`, group them
into columns/tiers by `level`, and color them by `status`. The unlock logic is
simple: a node changes from `locked` → `unlocked` when all edges pointing into
it are already `completed` (i.e., the learner has passed the checkpoint quiz).

## Sample tree — a concrete example

Suppose you drop in 5-6 introductory Machine Learning documents (a linear
algebra textbook, a calculus textbook, a statistics/probability textbook, and
a few ML chapters). After running the whole pipeline, the resulting tree
might look like this:

```
[Linear Algebra]      [Calculus]      [Probability & Statistics]
       │                   │                    │
       ▼                   ▼                    ▼
[Data Vectorization]  [Gradient Descent]  [Model Evaluation]
       │                   │                    │
       └─────────┬─────────┘                    │
                  ▼                              │
          [Linear Regression]                    │
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                        [Controlling Overfitting]
                                  │
                                  ▼
                        [Basic Neural Networks]
```

A few notes on this sample tree:

- **Tier 0 (foundation):** 3 concepts with no prerequisites — these are the nodes that unlock automatically as soon as the tree is created.
- **Tier 1:** Each node depends on exactly one Tier-0 node (e.g., "Data Vectorization" needs "Linear Algebra"). This is the result of step 4 (infer prerequisites) — the LLM is only asked about pairs pre-filtered by similarity, not every possible pair.
- **Linear Regression** (Tier 2) has two prerequisites converging — this illustrates exactly the point that a DAG allows multiple branches to merge, not just one straight line.
- **Controlling Overfitting** (Tier 3) has one edge that "jumps a tier" from Model Evaluation (Tier 1) — this is completely valid in a DAG, as long as the child's tier is always greater than every one of its parents' tiers.
- In practice, if step 5 (self-checking agent) detects a cycle — for example if the LLM mistakenly infers "Controlling Overfitting requires Linear Regression" (in reverse) — the agent automatically drops the edge with the lowest confidence in that cycle, without needing human intervention.

**On the unlock mechanism in the UI:** at the start, all 3 Tier-0 nodes are
unlocked. Once the learner passes the checkpoint quiz for "Linear Algebra,"
that node becomes `completed`; the system scans nodes with edges pointing to
it, checks whether all of its parents are already `completed`, and if so,
unlocks it. This is precisely why the pipeline carries `confidence` and
citation sources through end to end: they're not only needed for the
graph-repair algorithm, but also feed the Teach layer (lesson/quiz generated
via agentic RAG) displayed in the node detail panel.
