# Pipeline: Raw Documents → Mastery Tree

## Overview

The pipeline transforms a collection of raw documents (PDF/PPTX/DOCX) into a **structured Mastery Tree** (Skill Tree). In this tree, each node represents a learning concept, and each directed edge represents a **prerequisite** relationship (what must be learned first).

---

## The 6-Step Pipeline Architecture

The pipeline spans across two main services: the `gpu-worker` (which handles steps 1–4, primarily LLM inference and embeddings) and the `apps/api` (which handles steps 5–6, focusing on graph validation).

```text
[Raw Documents]
     │
     ▼  POST /ingest
[STEP 1: Document Chunking]
     │
     ▼  POST /embed
[STEP 2: Extract Raw Concepts]  ← Gemma LLM (Running on AMD GPU)
     │
     ▼
[STEP 3: Cluster & Dedupe]  ← Cosine similarity + Louvain community detection
     │
     ▼  POST /build-graph
[STEP 4: Infer Prerequisites]  ← Fireworks AI (Llama 3)
     │
     ▼
[STEP 5: Validate DAG]  ← Cycle detection (apps/api)
     │
     ▼
[STEP 6: Assign Levels]  ← Topological generations (apps/api)
     │
     ▼
[Complete Mastery Tree]
```

---

## Detailed Step-by-Step Breakdown

### STEP 1 — Chunk Documents
**Component:** `gpu-worker` (`worker/ingest.py`)

- **Input:** Raw file bytes (PDF, PPTX, DOCX).
- **Logic:** Splits files based on natural semantic boundaries rather than fixed character counts (to avoid cutting a concept in half).
  - **PDF:** 1 chunk per **page**.
  - **PPTX:** 1 chunk per **slide**.
  - **DOCX:** 1 chunk per **section** (divided by headings).
- **Output:** `chunks[]` — an array where each chunk has a `doc_id`, `chunk_id`, `page`, and `text`.

### STEP 2 — Extract Raw Concepts (Gemma LLM)
**Component:** `gpu-worker` (`worker/concepts.py`)

- **Input:** The list of `chunks[]` from Step 1.
- **Logic:** For each chunk, a prompt is sent to **Gemma** (served locally on an AMD GPU via Ollama/vLLM):
  > *"List the distinct learning concepts this text teaches. Return strict JSON..."*
- **Output:** `raw_concepts[]` — A raw, unnormalized list of concepts. This list will contain duplicates and varying phrasings (e.g., "Gradient Descent" and "Steepest Descent Algorithm").

### STEP 3 — Cluster & Dedupe (Embedding + Louvain)
**Component:** `gpu-worker` (`worker/concepts.py`)

- **Input:** `raw_concepts[]` (e.g., 150+ raw concepts).
- **Logic:** 
  1. **Embed:** Generates embeddings for all concepts using `bge-large` on ROCm.
  2. **Similarity:** Computes an N×N cosine similarity matrix.
  3. **Graphing:** Connects concepts with an edge if their similarity is >= 0.9.
  4. **Community Detection:** Runs the Louvain clustering algorithm; each community represents a group of synonymous concepts.
  5. **Canonicalization:** Selects a representative for the cluster (the one with the shortest name) and calculates the centroid embedding for the group.
- **Output:** `canonical_concepts[]` — A deduplicated list of concepts (e.g., ~40 concepts), preserving all source `chunk_ids` for accurate citations.

### STEP 4 — Infer Prerequisites (Fireworks AI / Llama)
**Component:** `gpu-worker` (`worker/prerequisites.py`)

- **Input:** `canonical_concepts[]` (including their centroid embeddings).
- **Logic:** 
  1. **Pre-filter Pairs:** Filters out irrelevant pairs by only evaluating concept pairs with a similarity >= 0.35. This critically reduces the complexity from O(n²) to a manageable subset (~100-200 pairs).
  2. **Inference:** For each valid pair, asks the LLM: *"Is A a prerequisite for B, vice versa, or neither? Return the direction and a confidence score."*
  3. **Edge Creation:** Creates a directed edge based on the LLM's response.
- **Output:** `candidate_edges[]` — A list of edges `{from, to, confidence}`.

### STEP 5 — Validate Graph (DAG Self-Correction)
**Component:** `apps/api` (`app/services/graph.py`)

- **Input:** `candidate_edges[]`.
- **Logic:** Constructs a directed graph (`networkx.DiGraph`). Because LLMs can occasionally infer contradictory loops (A → B → C → A), the system runs `nx.simple_cycles()`. If a cycle is detected, the agent **drops the edge with the lowest confidence score** within that cycle. This repeats until the graph is a valid Directed Acyclic Graph (DAG).
- **Output:** `valid_dag` — A cycle-free directed graph.

### STEP 6 — Assign Levels (Tiers)
**Component:** `apps/api` (`app/services/levels.py`)

- **Input:** `valid_dag`.
- **Logic:** Uses `nx.topological_generations()` to group the nodes into hierarchical tiers.
  - **Tier 0:** Foundations (no prerequisites).
  - **Tier 1:** Concepts depending directly on Tier 0.
  - **Tier N:** Progressively advanced concepts.
- **Output:** Finalized `nodes[]` (each assigned a `level` and `status`) and `edges[]`.

---

## Data Flow Summary

| Step | Input | Output | Core Technology |
|---|---|---|---|
| 1. Chunk | Raw bytes | `chunks[]` | PyMuPDF, python-pptx, python-docx |
| 2. Extract | `chunks[]` | `raw_concepts[]` | **Gemma** (Local AMD GPU) |
| 3. Dedupe | `raw_concepts[]` | `canonical_concepts[]` | Numpy + NetworkX (Louvain) |
| 4. Infer | `canonical_concepts[]` | `candidate_edges[]` | Fireworks AI (Llama 3) |
| 5. Validate | `candidate_edges[]` | `valid_dag` | NetworkX (Cycle detection) |
| 6. Level | `valid_dag` | `nodes[]` with tiers | NetworkX (Topological Gen) |

**Crucial Design Feature:** The `chunk_id` is preserved through every step of the pipeline. This ensures that every node in the final Skill Tree is intrinsically linked back to its source document (and specific page/slide). This traceability empowers both the self-checking graph logic and the subsequent step of agentic RAG generation for lessons and quizzes.
