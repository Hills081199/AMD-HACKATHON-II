# Session Handoff

## Verified Now

- What is currently working: the full "produce a tree" chain (feat-001 → feat-005) is implemented. `packages/gpu-worker`: `POST /ingest`, `POST /embed`, `POST /build-graph`. `apps/api`: `POST /graph/validate` (cycle repair), `apps/api/app/services/levels.py`'s `assign_levels()` (tiering, fully tested as a pure function), and `GET /trees/{topic_id}` now returns 200 with real tree data — but from the static sample file (`data/atlas_mastery_tree_sample.json`), not yet from a live run of the pipeline. `submit-quiz` still 501s (feat-008). `apps/web` is still placeholder pages (feat-006 is next).
- What verification actually ran: `cd apps/api && python -m pytest tests/` — 11/11 passed. `cd packages/gpu-worker && python -m pytest tests/` — 14/14 passed (regression check, unaffected by this session's changes). `python -m compileall app tests` in `apps/api` — pass. Did **not** run the full `./init.sh` (web deps still need `npm install`).

## Changed This Session

- Code or behavior added: `apps/api/app/services/levels.py` (`assign_levels`); `GET /trees/{topic_id}` in `apps/api/app/routers/trees.py` now serves the sample dataset instead of raising 501.
- Infrastructure or harness changes: none new (reused `apps/api`'s existing test setup from feat-004).
- Files modified: `apps/api/app/services/levels.py` (new), `apps/api/app/routers/trees.py`, `apps/api/tests/test_levels.py` (new), `apps/api/tests/test_trees_endpoint.py` (new), `feature_list.json`, `progress.md`.

## Broken Or Unverified

- Known defect: none found in the new tiering code.
- Unverified path: `GET /trees/{topic_id}` is not wired to a live pipeline run — same static file regardless of `topic_id`. `assign_levels()` has never processed a real feat-002/feat-004 output, only synthetic test fixtures. `apps/web` lint/build still unverified (node_modules not installed) — this is now a hard blocker for feat-006 being fully verified once built.
- Blockers for the next session: `npm install` in `apps/web` is needed before feat-006 can be lint/build-verified.

## Next Session

- Highest-priority unfinished feature: feat-006, "Skill-tree UI with unlock logic" — lives in `apps/web/app/tree/page.tsx` (currently `TODO: render mastery tree with @xyflow/react`).
- Why it is next: feat-005 (its only dependency) is now passing.
- What counts as passing: fetch `data/atlas_mastery_tree_sample.json` (dev) or `GET {NEXT_PUBLIC_API_URL}/trees/{topic_id}`, render with `@xyflow/react`, group nodes into columns by `level`, color by `status`. A node unlocks when every edge pointing into it has a `mastered`/completed source status.
- What must not change during that step: **reconcile the status-naming mismatch first** — the sample dataset uses `"completed"`, but `docs/concept-graph-pipeline.md`'s schema (and `apps/api/app/services/levels.py`'s output) uses `"locked"`/`"unlocked"` and implies `"mastered"` as the third state. Pick one vocabulary and use it consistently across the data file, the API, and the UI rather than papering over it with UI-side translation.
- Recommended Next Step: `cd apps/web && npm install`, confirm `npm run lint`/`npm run build` pass on the current placeholder pages first (establishes a clean baseline), then implement the tree view.

## Commands

- Startup: `./init.sh`
- Verification: see `CLAUDE.md` "Verification Commands"; per-feature checks live in `feature_list.json`.
- Focused debug command: `cd apps/api && python -m pytest tests/ -v`; `cd packages/gpu-worker && python -m pytest tests/ -v`; `uvicorn app.main:app --reload --port 8000` (from `apps/api`) to hit `GET /trees/intro-to-ml` manually.
