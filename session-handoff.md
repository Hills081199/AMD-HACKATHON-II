# Session Handoff

## Verified Now

- What is currently working: only scaffolding — `apps/web` (Next.js placeholder pages), `apps/api` (FastAPI app with a `/health` endpoint and a `trees` router that 501s on both routes), `packages/gpu-worker` (FastAPI app with a `/health` endpoint; `/embed` and `/build-graph` raise `NotImplementedError`). No pipeline stage is implemented yet.
- What verification actually ran: none against feature code this session (docs consolidation + harness scaffolding only). `./init.sh` has not been run yet — do that first next session to confirm the baseline (lint/build/compileall) is green before starting feat-001.

## Changed This Session

- Code or behavior added: none.
- Infrastructure or harness changes: added `CLAUDE.md`, `feature_list.json`, `progress.md`, `session-handoff.md`, `init.sh` (harness-creator scaffold); fixed a subshell-isolation bug in the generated `init.sh`.
- Files modified: consolidated `docs/` from 5 files to 4 (`brd.md`, `hackathon-scope.md`, `concept-graph-pipeline.md`, `architecture.md`) — see `progress.md` Session 001 for the full list of doc changes.

## Broken Or Unverified

- Known defect: none in application code (nothing is implemented yet to be broken).
- Unverified path: `./init.sh` itself hasn't been run end-to-end since the fix. The two Python `compileall` commands were manually verified this session and pass. The web `lint`/`build` commands were not run — `apps/web/node_modules` isn't installed yet; run `npm install` in `apps/web` before the first `./init.sh` call.
- Blockers for the next session: none. Day-1 ROCm/PyTorch compatibility check (docs/hackathon-scope.md §5) is the first real risk once GPU work starts.

## Next Session

- Highest-priority unfinished feature: feat-001, "Document ingest & chunking" (`packages/gpu-worker/worker/main.py`, `/embed` endpoint).
- Why it is next: every other pipeline stage (feat-002 through feat-009) depends on it, per `feature_list.json` dependencies.
- What counts as passing: feed a sample PDF/PPTX/DOCX from `data/` through `/embed` and get back `chunks[]` with `doc_id`/`page`/`chunk_id` populated, split on heading/slide boundaries — see the `verification` array on feat-001.
- What must not change during that step: don't start feat-002's Gemma/embedding logic in the same pass — keep ingest and embedding as separate, separately-verified steps per the harness's one-feature-at-a-time rule.
- Recommended Next Step: run `./init.sh` first, then implement feat-001.

## Commands

- Startup: `./init.sh`
- Verification: see `CLAUDE.md` "Verification Commands"; per-feature checks live in `feature_list.json`.
- Focused debug command: `cd packages/gpu-worker && uvicorn worker.main:app --reload --port 8100` then `curl -X POST localhost:8100/embed -d '{...}'` once feat-001 has real logic.
