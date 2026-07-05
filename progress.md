# Progress Log

## Current Verified State

- Last Updated: 2026-07-05
- Repository root: D:\AMD-HACKATHON-II
- Current Objective: Build the concept-dependency-graph pipeline end to end (feat-001 → feat-009 in `feature_list.json`). feat-001, feat-002, and feat-003 are now passing; feat-004 (self-checking graph agent) is next, in `apps/api`.
- Standard startup path: `./init.sh`
- Standard verification path: see "Verification Commands" in `CLAUDE.md` — web lint/build, api/gpu-worker `compileall`, and `cd packages/gpu-worker && python -m pytest tests/` (14/14 passing). Only gpu-worker has a real test suite so far; `apps/api` still has no tests — feat-004 should add one.
- Highest-priority unfinished feature: feat-004, "Self-checking graph agent (cycle/redundancy repair)"
- Blockers: none currently. Day-1 risk flagged in `docs/hackathon-scope.md` §5: verify ROCm/PyTorch compatibility on the AMD Developer Cloud box before relying on it. feat-002/feat-003 were verified with fakes (no live Gemma/Ollama server, model download, or Fireworks API key) — worth a real-infra pass once ROCm and Fireworks credentials are provisioned.
- Recommended Next Step: in `apps/api`, build a `networkx.DiGraph` from feat-003's `candidate_edges[]`, run `nx.simple_cycles()`, and repair any cycle found by dropping its lowest-confidence edge (bounded retry loop; force-drop the weakest edge if a cycle survives N iterations) — see docs/concept-graph-pipeline.md step 5.

## Session Log

### Session 001

- Date: 2026-07-05
- Goal: Consolidate and de-duplicate `docs/` (5 overlapping/contradictory documents → 4 consistent ones), then scaffold a minimal harness.
- Completed:
  - Merged `Approach...md` + `Concept_Graph_Engine_Detail.md` → `docs/concept-graph-pipeline.md`.
  - Split the concatenated `Atlas_Hackathon_Feature_Prioritization.md` into a pitch section (moved to `docs/brd.md`) and a scope doc (`docs/hackathon-scope.md`), renumbered, merged its two redundant 7-day plans into one.
  - Rewrote `docs/BRD_Ver_1.0_Atlas.md` → `docs/brd.md`: replaced the gamification/flashcards/Postgres MVP scope with the actual graph/skill-tree MVP scope (added §7.1b Post-MVP Roadmap), fixed tech stack to match the real repo (Next.js, SQLite/JSON, Gemma served locally on ROCm), resolved 4 of 6 open clarifying questions.
  - Updated `docs/architecture.md` to link out instead of duplicating pipeline detail.
  - Created harness scaffold via `harness-creator` skill: `CLAUDE.md`, `feature_list.json` (feat-001..009, mapped from `docs/hackathon-scope.md` §4 P0 table), `progress.md`, `session-handoff.md`, `init.sh`.
  - Fixed a bug in the generated `init.sh` (each `cd` line wasn't subshell-isolated, so the second `cd apps/web` would have failed on the third command).
- Verification run: manually ran the two Python commands (`cd apps/api && python -m compileall app`, `cd packages/gpu-worker && python -m compileall worker`) — both pass. Did not run the web `lint`/`build` commands or the full `./init.sh` — `apps/web/node_modules` isn't installed yet (`npm install` needed first). Next session should install web deps and run `./init.sh` once before starting feat-001.
- Evidence captured: none (no feature work done this session — this was a docs/harness session).
- Commits: none made this session (docs and harness files are on disk, uncommitted).
- Files or artifacts updated: see "Completed" above, plus this harness scaffold.
- Known risk or unresolved issue: two `brd.md` clarifying questions remain genuinely open (primary target audience; public-track sharing/licensing) — see `docs/brd.md` §2.1.
- Next best step: run `./init.sh` to confirm the baseline is green, then start feat-001 (ingest & chunking) in `packages/gpu-worker`.

### Session 002

- Date: 2026-07-05
- Goal: Implement feat-001, "Document ingest & chunking."
- Completed: Added `packages/gpu-worker/worker/ingest.py` (`chunk_document()` dispatching to PDF/PPTX/DOCX parsers, chunking by page/slide/heading boundary rather than a hard character count); wired a new `POST /ingest` endpoint in `worker/main.py` (kept `/embed` reserved for feat-002); added parsing deps (`pymupdf`, `python-pptx`, `python-docx`, `python-multipart`) to `requirements.txt` and a new `requirements-dev.txt` for `pytest`; added `packages/gpu-worker/tests/test_ingest.py` with synthetic PDF/PPTX/DOCX fixtures.
- Verification run: `python -m compileall worker tests` (pass); `python -m pytest tests/` — 4/4 passed; manually exercised `POST /ingest` via FastAPI `TestClient` with a synthetic PDF (200, correct chunk shape).
- Evidence captured: recorded in `feature_list.json` feat-001 `evidence[]`.
- Commits: not yet committed this session.
- Files or artifacts updated: `packages/gpu-worker/worker/ingest.py` (new), `packages/gpu-worker/worker/main.py`, `packages/gpu-worker/requirements.txt`, `packages/gpu-worker/requirements-dev.txt` (new), `packages/gpu-worker/tests/test_ingest.py` (new), `init.sh`, `CLAUDE.md`, `feature_list.json`.
- Known risk or unresolved issue: no real sample PDF/PPTX/DOCX exists in `data/` yet — tests use synthetic in-memory fixtures. Re-verify against the actual demo dataset once feat-009 picks one. docx chunks use a heading-delimited section index as `page` (no true page number available without rendering) — documented in `ingest.py` and worth flagging in the demo if judges ask.
- Next best step: implement feat-002 (embedding + local Gemma concept extraction + clustering) on top of `chunk_document()`.

### Session 003

- Date: 2026-07-05
- Goal: Implement feat-002, "Embedding + concept extraction & clustering."
- Completed: Added `packages/gpu-worker/worker/concepts.py` — `GemmaConceptExtractor` (HTTP client against a local Ollama-style endpoint, `GEMMA_BASE_URL` env var, default `http://localhost:11434`, no hosted-API path), `SentenceTransformerEmbedder` (lazy-loaded `bge-large-en-v1.5`), and `cluster_concepts` (cosine similarity + `networkx.algorithms.community.louvain_communities`, no LLM call, per docs/concept-graph-pipeline.md step 3). Wired `POST /embed` in `worker/main.py` via FastAPI `Depends` (`get_gemma_extractor`, `get_embedder`) so both can be swapped for fakes in tests. Added `tests/test_concepts.py` (4 tests) and `tests/test_main_embed.py` (endpoint-level test using `app.dependency_overrides`). Added `numpy`/`httpx` to `requirements.txt` (previously only transitive deps).
- Verification run: `python -m compileall worker tests` (pass); `python -m pytest tests/` — 9/9 passed (4 feat-001 + 5 feat-002, no regressions).
- Evidence captured: recorded in `feature_list.json` feat-002 `evidence[]`, including the specific assertion that `GemmaConceptExtractor` posts to `{base_url}/api/generate` (a regression to a hosted API URL would fail that test) and the near-duplicate-merge clustering test ("gradient descent" vs "the steepest-descent optimization algorithm").
- Commits: not yet committed this session.
- Files or artifacts updated: `packages/gpu-worker/worker/concepts.py` (new), `packages/gpu-worker/worker/main.py`, `packages/gpu-worker/requirements.txt`, `packages/gpu-worker/tests/test_concepts.py` (new), `packages/gpu-worker/tests/test_main_embed.py` (new), `feature_list.json`.
- Known risk or unresolved issue: not verified against a real local Gemma/Ollama server or a real sentence-transformers model download — both are behind fakes in the test suite by design. Concept embeddings aren't cached/returned from `/embed`; feat-003 will need embeddings again for pair pre-filtering, so recomputation cost is worth watching.
- Next best step: implement feat-003 (Fireworks-based prerequisite inference with O(n²)-avoidance pre-filtering) in `apps/api`.

### Session 004

- Date: 2026-07-05
- Goal: Implement feat-003, "Dependency-graph construction (prerequisite inference)."
- Completed: Discovered and fixed an inconsistency between `feature_list.json` (which said feat-003 lives in `apps/api`) and `docs/architecture.md`'s Data contract section (which says `gpu-worker` produces the candidate graph including inferred edges, and `api` starts at the self-checking loop) — corrected `feature_list.json`'s `area` to `gpu-worker` and implemented there instead. Gave `CanonicalConcept` (feat-002) an `id` (`concept_NNN`) and `embedding` (cluster centroid) field so `/embed`'s output carries what pre-filtering needs, without apps/api needing its own embedding model. Added `packages/gpu-worker/worker/prerequisites.py`: `pre_filter_pairs` (cosine similarity over concept embeddings) and `FireworksClient` (hosted OpenAI-compatible chat completions — a hosted call is fine here, unlike Gemma) and `build_candidate_edges`. Wired `POST /build-graph` via FastAPI `Depends`. Added `tests/test_prerequisites.py` (4 tests, including one that directly proves the O(n²) avoidance: 6 concepts, C(6,2)=15 possible pairs, but only 3 pre-filtered pairs are ever sent to the fake Fireworks client) and `tests/test_main_build_graph.py` (endpoint-level).
- Verification run: `python -m compileall worker tests` (pass); `python -m pytest tests/` — 14/14 passed (4 feat-001 + 5 feat-002 + 5 feat-003, no regressions after the `CanonicalConcept` schema change).
- Evidence captured: recorded in `feature_list.json` feat-003 `evidence[]`, including the exact call-count proof for the O(n²)-avoidance verification bullet. Also corrected feat-002's stale note (previously said embeddings weren't returned from `/embed` — now they are).
- Commits: not yet committed this session.
- Files or artifacts updated: `packages/gpu-worker/worker/concepts.py` (CanonicalConcept: +id, +embedding), `packages/gpu-worker/worker/prerequisites.py` (new), `packages/gpu-worker/worker/main.py`, `packages/gpu-worker/tests/test_prerequisites.py` (new), `packages/gpu-worker/tests/test_main_build_graph.py` (new), `feature_list.json`, `progress.md`.
- Known risk or unresolved issue: not verified against a real Fireworks API key/live endpoint — `FireworksClient` is only verified against a monkeypatched `httpx.post`. `candidate_edges[]` haven't been spot-checked against the actual sample tree in `docs/concept-graph-pipeline.md` yet (needs a real Fireworks key + a real feat-002 run); do that once feat-009 picks the demo dataset. Edge `from`/`to` use concept `id` (e.g. `concept_001`), not name — worth confirming that's what feat-004/feat-005/feat-006 expect downstream.
- Next best step: implement feat-004 (self-checking graph agent — cycle detection + repair loop) in `apps/api`, consuming feat-003's `candidate_edges[]`.
