"""AMD GPU / ROCm worker.

Responsibilities (see docs/concept-graph-pipeline.md for the full 6-step
breakdown, and docs/architecture.md's "Data contract" section for why steps
1-4 all live here rather than in apps/api):
  1. Chunk incoming documents (POST /ingest).
  2. Embed chunks (sentence-transformers on ROCm-enabled torch) and extract
     concepts via Gemma served locally, then cluster/dedupe (POST /embed).
  3. Infer prerequisite edges between concepts via Fireworks, pre-filtered by
     embedding similarity to avoid an O(n^2) call scan (POST /build-graph).
     apps/api picks up from here: self-checking validation (step 5) onward.
"""

import os

from fastapi import Depends, FastAPI, File, UploadFile

from worker.concepts import (
    GemmaConceptExtractor,
    OpenAIConceptExtractor,
    OpenAIEmbedder,
    SentenceTransformerEmbedder,
    cluster_concepts,
    extract_raw_concepts,
)
from worker.ingest import Chunk, chunk_document
from worker.prerequisites import FireworksClient, build_candidate_edges

app = FastAPI(title="Atlas GPU Worker")

# LLM_PROVIDER=openai is a prototyping-only switch to validate the pipeline
# end-to-end against GPT-4o mini before real ROCm/Gemma infrastructure is
# available (docs/hackathon-scope.md §5) — NOT the production path (see
# GemmaConceptExtractor/OpenAIConceptExtractor's docstrings).
_USE_OPENAI = os.environ.get("LLM_PROVIDER", "").lower() == "openai"
_embedder = OpenAIEmbedder() if _USE_OPENAI else SentenceTransformerEmbedder()
_gemma = (
    OpenAIConceptExtractor()
    if _USE_OPENAI
    else GemmaConceptExtractor(base_url=os.environ.get("GEMMA_BASE_URL", "http://localhost:11434"))
)
_fireworks = FireworksClient()


def get_embedder():
    return _embedder


def get_gemma_extractor():
    return _gemma


def get_fireworks_client() -> FireworksClient:
    return _fireworks


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
def embed(payload: dict, gemma=Depends(get_gemma_extractor), embedder=Depends(get_embedder)):
    """Pipeline steps 2-3 — concept extraction (local Gemma) + clustering. See
    docs/concept-graph-pipeline.md steps 2-3. Takes /ingest's chunks[] output."""
    chunks = [Chunk(**chunk) for chunk in payload["chunks"]]
    raw_concepts = extract_raw_concepts(chunks, gemma)
    canonical_concepts = cluster_concepts(raw_concepts, embedder)
    return {"concepts": [concept.to_dict() for concept in canonical_concepts]}


@app.post("/build-graph")
def build_graph(payload: dict, fireworks=Depends(get_fireworks_client)):
    """Pipeline step 4 — prerequisite inference (Fireworks), pre-filtered by
    embedding similarity. See docs/concept-graph-pipeline.md step 4. Takes
    /embed's concepts[] output (each with an id and embedding)."""
    edges = build_candidate_edges(payload["concepts"], fireworks)
    return {"edges": edges}
