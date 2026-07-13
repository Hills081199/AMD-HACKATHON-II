# Session Handoff

## Verified Now

- What is currently working: the full loop from documents to a playable, quizzable tree exists end to end for the static sample dataset. `apps/web/app/tree/page.tsx` fetches `GET {NEXT_PUBLIC_API_URL}/trees/{topic_id}`, renders the mastery tree via `@xyflow/react`, colors nodes by derived status (locked/unlocked/completed), and opens a real checkpoint-quiz modal on an unlocked node — passing it marks the node completed and unlocks its children live, failing it keeps the node unlocked (not completed) with children still locked. `apps/api`: `POST /graph/validate`, `assign_levels()`, `GET /trees/{topic_id}` (static sample), `POST /trees/{topic_id}/nodes/{node_id}/lesson` (feat-007, agentic-RAG lesson/quiz/example generation with a self-check retry loop), `POST /trees/{topic_id}/nodes/{node_id}/submit-quiz` (feat-008, real MCQ grading). `packages/gpu-worker`: `POST /ingest`, `POST /embed`, `POST /build-graph`.
- What verification actually ran: `npm run lint` / `npm run build` in `apps/web` (both clean). `cd apps/api && python -m pytest tests/` — 23/23. `cd packages/gpu-worker && python -m pytest tests/` — 14/14. `python -m pytest scripts/tests/` (new, feat-009's pipeline-runner tests) — 3/3. Additionally, for feat-008: started both `apps/api` and `apps/web` in the background, drove a real Chromium session (Playwright, installed temporarily then removed) against `/tree`, submitted a wrong quiz answer (confirmed the fail message and no state change) and then the correct one (confirmed "Passed!", the node turning green, and its child flipping from locked/grey to unlocked/blue), with zero browser console errors once a stale orphaned uvicorn process from an earlier session was found and killed.
- feat-001 through feat-008 are `passing` in `feature_list.json`. feat-009 is `blocked` — see below.

## Changed This Session (most recent: feat-009)

- Code or behavior added: `scripts/generate_sample_docs.py` (authors a real 5-document intro-ML source set), `scripts/build_demo_dataset.py` (orchestrates feat-001→feat-007's already-tested functions into the final tree JSON schema; requires real `GEMMA_BASE_URL`/`FIREWORKS_API_KEY`, refuses to run without them), `scripts/tests/test_build_demo_dataset.py` (verifies the orchestration with fakes over the real checked-in documents).
- Infrastructure or harness changes: added the real source documents at `data/source_docs/` (checked in). Added `GEMMA_BASE_URL` to `.env.example` (was missing). Added `data/generated/` to `.gitignore` (the script's default output path — not checked in until a specific run is deliberately promoted to replace the sample dataset).
- Files modified: see `progress.md` Session 010 for the full list, plus feat-007 (Session 008) and feat-008 (Session 009) changes in `apps/api` and `apps/web/app/tree/`.

## Broken Or Unverified

- Known defect: none found in the new code this session.
- Unverified path: feat-009's actual credentialed pipeline run has never happened — this environment has no reachable local Gemma/Ollama server and no Fireworks API key. The orchestration logic is verified with fakes (same pattern as feat-002/003/007's own tests), but not the judgment quality of a real run's output.
- Blockers for the next session: feat-009 needs `GEMMA_BASE_URL` (a running local Gemma/Ollama server) and `FIREWORKS_API_KEY` to actually run `scripts/build_demo_dataset.py` for real. This is the same Day-1 ROCm/credentials risk flagged in `docs/hackathon-scope.md` §5 since Session 001.

## Next Session

- Highest-priority unfinished feature: feat-009, "Pre-indexed, deterministic demo dataset" — the only feature not `passing`.
- Why it is next: it's the last one in `feature_list.json`, and every other feature (feat-001–008) is done and passing.
- What counts as unblocking it: run `python scripts/build_demo_dataset.py` for real once `GEMMA_BASE_URL`/`FIREWORKS_API_KEY` are available; inspect the output for plausibility against `docs/concept-graph-pipeline.md`'s sample tree; decide whether/how to promote it to replace `data/atlas_mastery_tree_sample.json`.
- What must not change during that step: don't swap the checked-in sample file for generated output without also updating `apps/api/tests/test_trees_endpoint.py` and `test_trees_submit_quiz_endpoint.py`, which hardcode specific node/question IDs (`n3`, `q_n3_1`, etc.) from the current hand-written file — do both in the same pass, or those tests will fail for the wrong reason.
- Recommended Next Step: if real credentials become available, run the script, review its output, and only then decide on promotion + test updates together. If credentials are still unavailable, there is no further useful code to write here — the harness's own rule is "document why it is blocked" rather than force a fake pass, which is what this session did.

## Commands

- Startup: `./init.sh`
- Verification: see `CLAUDE.md` "Verification Commands"; per-feature checks live in `feature_list.json`. Also: `python -m pytest scripts/tests/` (feat-009, not yet folded into the fixed list).
- Focused debug command: `cd apps/web && npm run dev` then open `http://localhost:3000/tree` (needs `apps/api` running on port 8000 too — `cd apps/api && uvicorn app.main:app --reload --port 8000`). `cd apps/api && python -m pytest tests/ -v`; `cd packages/gpu-worker && python -m pytest tests/ -v`.
- Generating the demo dataset (once credentials exist): `GEMMA_BASE_URL=... FIREWORKS_API_KEY=... python scripts/build_demo_dataset.py`.
