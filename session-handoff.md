# Session Handoff

## Verified Now

- What is currently working: the full candidate-graph-to-valid-DAG chain now exists. `packages/gpu-worker`: `POST /ingest` (chunking), `POST /embed` (embedding + local-Gemma concept extraction + clustering, returns concept `id`/`embedding`), `POST /build-graph` (Fireworks prerequisite inference, pre-filtered by similarity). `apps/api`: `POST /graph/validate` (cycle detection + repair, with an auditable drop log) is new this session. `apps/api`'s `trees` router still 501s on both routes (`GET /{topic_id}`, `submit-quiz`) — that's feat-005/006/008's job. `apps/web` is still placeholder pages.
- What verification actually ran: `cd apps/api && python -m pytest tests/` — 6/6 passed (first real test suite for `apps/api`). `cd packages/gpu-worker && python -m pytest tests/` — 14/14 passed, re-run to confirm no regressions. `python -m compileall app tests` in `apps/api` — pass. Did **not** run the full `./init.sh` this session (web deps still need `npm install`, unchanged from previous sessions).

## Changed This Session

- Code or behavior added: `apps/api/app/services/graph.py` (`build_graph`, `repair_cycles`, `validate_graph`); new `POST /graph/validate` endpoint (`apps/api/app/routers/graph.py`), mounted in `app/main.py`.
- Infrastructure or harness changes: `apps/api` got its first test suite — added `apps/api/requirements-dev.txt` (pytest, mirroring `packages/gpu-worker`'s pattern) and wired `cd apps/api && python -m pytest tests/` into `init.sh` and `CLAUDE.md`.
- Files modified: `apps/api/app/services/__init__.py` (new), `apps/api/app/services/graph.py` (new), `apps/api/app/routers/graph.py` (new), `apps/api/app/main.py`, `apps/api/requirements-dev.txt` (new), `apps/api/tests/__init__.py` (new), `apps/api/tests/test_graph.py` (new), `apps/api/tests/test_graph_endpoint.py` (new), `init.sh`, `CLAUDE.md`, `feature_list.json`, `progress.md`.

## Broken Or Unverified

- Known defect: none found in the new cycle-repair code.
- Unverified path: `repair_cycles`/`validate_graph` have only been exercised against small synthetic edge lists (hand-built cycles), not a real candidate-edge set produced by a live feat-003 run against Fireworks. `nx.simple_cycles()`'s worst-case exponential cost hasn't been stress-tested against a larger/denser graph. `apps/web` lint/build still unverified (node_modules not installed).
- Blockers for the next session: none.

## Next Session

- Highest-priority unfinished feature: feat-005, "Topological sort → tiered learning path" — lives in `apps/api`, consuming feat-004's `valid_dag` (the `edges` from `validate_graph`'s output).
- Why it is next: feat-004 (its only dependency) is now passing.
- What counts as passing: use `nx.topological_generations()` (not a plain `topological_sort` — the pipeline deliberately wants tiers/parallel branches, not one straight line) to assign each node a `level`; every edge's child level must be strictly greater than its parent's level. Wire `GET /trees/{topic_id}` in `apps/api/app/routers/trees.py` to return real `nodes[]`/`edges[]` matching the schema in `docs/concept-graph-pipeline.md`, replacing its current `HTTPException(501)`.
- What must not change during that step: don't start feat-006's frontend rendering work in the same pass — feat-005 is API-only (produce correct `nodes[]` with `level`, still isolated from the UI). Note that `build_graph`'s edges-only construction (feat-004) won't include isolated/no-edge concept nodes — feat-005 will need the full concept list (from feat-002's output) to include those as standalone tier-0 nodes, not just nodes that happen to have an edge.
- Recommended Next Step: add a `assign_levels(concepts, edges)` function (probably in a new `apps/api/app/services/levels.py` or extending `graph.py`) that takes feat-002's full concept list plus feat-004's repaired edges and produces `nodes[]` with `level`/`status`, then wire it into `GET /trees/{topic_id}`.

## Commands

- Startup: `./init.sh`
- Verification: see `CLAUDE.md` "Verification Commands"; per-feature checks live in `feature_list.json`.
- Focused debug command: `cd apps/api && python -m pytest tests/ -v` for the API suite; `cd packages/gpu-worker && python -m pytest tests/ -v` for the GPU worker suite; `uvicorn app.main:app --reload --port 8000` (from `apps/api`) to run the API manually.
