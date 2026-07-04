# Atlas — architecture

## Pipeline stages

| Stage | What happens | Runs on |
|---|---|---|
| Ingest | Upload documents, chunk | Cloud (apps/api) |
| Understand | Embeddings, concept extraction & clustering | AMD GPU / ROCm (packages/gpu-worker) |
| Structure | Build concept-dependency graph + self-checking agent | AMD GPU / ROCm + Fireworks AI |
| Order | Topological sort → optimal learning path | Cloud, lightweight (apps/api, networkx) |
| Teach | Agentic RAG: mini-lesson + quiz + real-world example per node | Fireworks AI |
| Play | Skill-tree UI, checkpoints, unlock logic | Next.js (apps/web) |

## Why this split

Heavy, batched, latency-tolerant work (embeddings, clustering, graph
construction) runs on the AMD GPU. Reasoning steps (prerequisite inference,
lesson/quiz generation, agentic self-checks) run on Fireworks AI. This keeps
the GPU busy with what GPUs are good at, and keeps reasoning on a fast hosted
LLM API — a genuine hybrid split rather than one remote API call end to end.

## Data contract between services

- `gpu-worker` produces a candidate graph (nodes + inferred prerequisite
  edges) and hands it to `api`.
- `api` runs the self-checking validation loop (via Fireworks), then
  `networkx.topological_sort`, then calls Fireworks again per node for
  lesson/quiz/example generation.
- `api` serves the final tree as JSON to `web` — see
  [`/data/atlas_mastery_tree_sample.json`](../data/atlas_mastery_tree_sample.json)
  for the exact shape the frontend should expect.

## Diagram

See the pipeline and kotaemon-integration diagrams shared in the project
discussion — reproduce them here as images if you want them in the README
for the pitch deck.
