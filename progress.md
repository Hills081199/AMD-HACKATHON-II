# Progress Log

## Current Verified State

- Last Updated: 2026-07-05
- Repository root: D:\AMD-HACKATHON-II
- Current Objective: Build the concept-dependency-graph pipeline end to end (feat-001 → feat-009 in `feature_list.json`). feat-001 is now passing; feat-002 (embedding + concept extraction + clustering) is next.
- Standard startup path: `./init.sh`
- Standard verification path: see "Verification Commands" in `CLAUDE.md` — web lint/build, api/gpu-worker `compileall`, and (new) `cd packages/gpu-worker && python -m pytest tests/`. Only gpu-worker has a real test suite so far; other features still rely on their own `verification` steps in `feature_list.json` until tests are added for them too.
- Highest-priority unfinished feature: feat-002, "Embedding + concept extraction & clustering"
- Blockers: none currently. Day-1 risk flagged in `docs/hackathon-scope.md` §5: verify ROCm/PyTorch compatibility on the AMD Developer Cloud box before relying on it.
- Recommended Next Step: implement embedding (sentence-transformers) + Gemma-based concept extraction (local vLLM-ROCm/Ollama) + clustering/dedupe in `packages/gpu-worker/worker/main.py`'s `/embed` endpoint, consuming `chunk_document()` output from feat-001.

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
