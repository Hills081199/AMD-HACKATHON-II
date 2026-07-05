# Session Handoff

## Verified Now

- What is currently working: `packages/gpu-worker`'s `POST /ingest` endpoint accepts multipart PDF/PPTX/DOCX uploads and returns `chunks[]` with `doc_id`/`chunk_id`/`page`/`text`, chunked by page/slide/heading boundary (feat-001, passing). Everything else is still scaffolding: `apps/web` (Next.js placeholder pages), `apps/api` (FastAPI app with `/health` and a `trees` router that 501s on both routes), `packages/gpu-worker`'s `/embed` and `/build-graph` still raise `NotImplementedError` (reserved for feat-002+).
- What verification actually ran: `cd packages/gpu-worker && python -m pytest tests/` — 4/4 passed. `python -m compileall worker tests` — pass. Manually exercised `POST /ingest` via FastAPI `TestClient` with a synthetic PDF and got the expected chunk back. Did **not** run the full `./init.sh` this session (web deps still need `npm install`, unchanged from last session).

## Changed This Session

- Code or behavior added: `packages/gpu-worker/worker/ingest.py` (`chunk_document()` for PDF/PPTX/DOCX); `POST /ingest` endpoint in `worker/main.py`.
- Infrastructure or harness changes: added `pymupdf`/`python-pptx`/`python-docx`/`python-multipart` to `packages/gpu-worker/requirements.txt`; added `packages/gpu-worker/requirements-dev.txt` (pytest, not installed in the runtime container); added the pytest command to `init.sh` and `CLAUDE.md`'s verification list.
- Files modified: `packages/gpu-worker/worker/ingest.py` (new), `packages/gpu-worker/worker/main.py`, `packages/gpu-worker/requirements.txt`, `packages/gpu-worker/requirements-dev.txt` (new), `packages/gpu-worker/tests/test_ingest.py` (new), `init.sh`, `CLAUDE.md`, `feature_list.json`, `progress.md`.

## Broken Or Unverified

- Known defect: none found in the new ingest code.
- Unverified path: no real sample PDF/PPTX/DOCX exists in `data/` yet — feat-001 was verified against synthetic in-memory fixtures built in the test file, not a real document. `apps/web` lint/build still unverified (node_modules not installed).
- Blockers for the next session: none. Day-1 ROCm/PyTorch compatibility check (docs/hackathon-scope.md §5) is still the first real risk once GPU embedding/Gemma work starts in feat-002.

## Next Session

- Highest-priority unfinished feature: feat-002, "Embedding + concept extraction & clustering" (`packages/gpu-worker/worker/main.py`, `/embed` endpoint).
- Why it is next: feat-001 (its only dependency) is now passing.
- What counts as passing: `/embed` takes `chunk_document()` output, produces embeddings via sentence-transformers, extracts `raw_concepts[]` per chunk via Gemma served **locally** (vLLM-ROCm/Ollama — not a hosted API, this is judging-critical, see feat-002's verification notes), then clusters/dedupes into `canonical_concepts[]` via cosine similarity + Louvain (no LLM call needed for that half).
- What must not change during that step: don't start feat-003's Fireworks prerequisite-inference logic in the same pass — keep embedding/extraction/clustering and prerequisite inference as separate, separately-verified steps.
- Recommended Next Step: install `packages/gpu-worker/requirements-dev.txt`, confirm `python -m pytest tests/` still passes (regression check), then implement feat-002.

## Commands

- Startup: `./init.sh`
- Verification: see `CLAUDE.md` "Verification Commands"; per-feature checks live in `feature_list.json`.
- Focused debug command: `cd packages/gpu-worker && python -m pytest tests/ -v` for the ingest suite; `uvicorn worker.main:app --reload --port 8100` to run the service manually.
