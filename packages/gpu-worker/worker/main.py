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

from fastapi import FastAPI, File, UploadFile

from worker.ingest import chunk_document

app = FastAPI(title="Atlas GPU Worker")


@app.get("/health")
def health():
    return {"status": "ok", "device": "TODO: report torch.cuda/rocm device info"}


@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    """Pipeline step 1 — chunk & embed (chunking half). See
    docs/concept-graph-pipeline.md step 1."""
    chunks = []
    for upload in files:
        content = await upload.read()
        chunks.extend(chunk_document(upload.filename, content))
    return {"chunks": [chunk.to_dict() for chunk in chunks]}


@app.post("/embed")
def embed(payload: dict):
    raise NotImplementedError("TODO: embed chunks + extract/cluster concepts on GPU (Gemma, local ROCm)")


@app.post("/build-graph")
def build_graph(payload: dict):
    raise NotImplementedError("TODO: concept extraction, clustering, candidate graph edges")
