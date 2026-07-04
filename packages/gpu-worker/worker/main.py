"""AMD GPU / ROCm worker.

Responsibilities (see docs/architecture.md — the "Understand" and "Structure"
stages):
  1. Chunk + embed incoming documents (sentence-transformers on ROCm-enabled torch).
  2. Extract & cluster concepts from the embedded chunks.
  3. Build the candidate concept-dependency graph (edges refined/validated by
     the self-checking agent that calls out to Fireworks — see apps/api).

This file is a placeholder entrypoint; wire it up to an actual FastAPI or
task-queue worker depending on how apps/api dispatches jobs.
"""

from fastapi import FastAPI

app = FastAPI(title="Atlas GPU Worker")


@app.get("/health")
def health():
    return {"status": "ok", "device": "TODO: report torch.cuda/rocm device info"}


@app.post("/embed")
def embed(payload: dict):
    raise NotImplementedError("TODO: chunk + embed documents on GPU")


@app.post("/build-graph")
def build_graph(payload: dict):
    raise NotImplementedError("TODO: concept extraction, clustering, candidate graph edges")
