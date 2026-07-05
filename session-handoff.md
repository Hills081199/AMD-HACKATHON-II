# Session Handoff

## Verified Now

- What is currently working: `packages/gpu-worker` now implements the whole "produce a candidate graph" half of the pipeline — `POST /ingest` (feat-001, chunking), `POST /embed` (feat-002, embedding + local-Gemma concept extraction + clustering, now also returning each concept's `id` and `embedding`), and `POST /build-graph` (feat-003, Fireworks-based prerequisite inference, pre-filtered by embedding similarity to avoid an O(n²) call scan). `apps/api` is still scaffolding (`/health` only; `trees` router 501s on both routes) — it picks up from feat-004 (self-checking validation) onward, per `docs/architecture.md`'s Data contract section. `apps/web` is still placeholder pages.
- What verification actually ran: `cd packages/gpu-worker && python -m pytest tests/` — 14/14 passed (4 feat-001 + 5 feat-002 + 5 feat-003, no regressions from the `CanonicalConcept` schema change). `python -m compileall worker tests` — pass. Did **not** run the full `./init.sh` this session (web deps still need `npm install`, unchanged from previous sessions).

## Changed This Session

- Code or behavior added: `packages/gpu-worker/worker/prerequisites.py` (`FireworksClient`, `pre_filter_pairs`, `build_candidate_edges`); wired `POST /build-graph` via FastAPI `Depends`. `CanonicalConcept` (in `concepts.py`) gained `id` and `embedding` fields, now included in `/embed`'s response.
- Infrastructure or harness changes: none new this session (no new deps — `httpx`/`numpy` were already added for feat-002).
- Files modified: `packages/gpu-worker/worker/concepts.py`, `packages/gpu-worker/worker/prerequisites.py` (new), `packages/gpu-worker/worker/main.py`, `packages/gpu-worker/tests/test_prerequisites.py` (new), `packages/gpu-worker/tests/test_main_build_graph.py` (new), `feature_list.json`, `progress.md`.
- Also fixed: `feature_list.json`'s feat-003 `area` was `"api"`, contradicting `docs/architecture.md`'s explicit Data contract (gpu-worker produces the candidate graph, api starts at self-checking). Corrected to `"gpu-worker"` and implemented there.

## Broken Or Unverified

- Known defect: none found in the new prerequisite-inference code.
- Unverified path: `FireworksClient` has never hit a real Fireworks endpoint — only a monkeypatched `httpx.post`. `candidate_edges[]` haven't been spot-checked against the actual sample tree in `docs/concept-graph-pipeline.md` (that needs a real Fireworks key + a real feat-002 run on real documents, not synthetic fixtures). `apps/web` lint/build still unverified (node_modules not installed).
- Blockers for the next session: none. Will need a `FIREWORKS_API_KEY` in `.env` before any real (non-test) run of `/build-graph`.

## Next Session

- Highest-priority unfinished feature: feat-004, "Self-checking graph agent (cycle/redundancy repair)" — lives in `apps/api`, consuming feat-003's `candidate_edges[]`.
- Why it is next: feat-003 (its only dependency) is now passing.
- What counts as passing: build a `networkx.DiGraph` from `candidate_edges[]`, run `nx.simple_cycles()`; if a cycle is found, drop its lowest-confidence edge and repeat (bounded retry loop; force-drop the weakest edge if a cycle survives N iterations), producing a `valid_dag` with zero cycles — log which edges were auto-dropped and why (this repair-loop transparency is the actual "agentic" story for judging, don't skip it).
- What must not change during that step: don't start feat-005's `topological_generations()`/tiering logic in the same pass — keep cycle-repair and level-assignment as separate, separately-verified steps. This is also the first feature to touch `apps/api` — it has no test suite yet, so add one (mirror the `packages/gpu-worker/tests/` pattern: fakes for Fireworks re-evaluation calls, no live network needed).
- Recommended Next Step: implement the repair loop in `apps/api` (e.g. a new `app/services/graph.py`), wire it behind an endpoint or internal call from the `trees` flow, and add `apps/api/tests/`.

## Commands

- Startup: `./init.sh`
- Verification: see `CLAUDE.md` "Verification Commands"; per-feature checks live in `feature_list.json`.
- Focused debug command: `cd packages/gpu-worker && python -m pytest tests/ -v` for the full gpu-worker suite; `uvicorn worker.main:app --reload --port 8100` to run the service manually.
