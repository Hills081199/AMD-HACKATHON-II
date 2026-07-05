# Session Handoff

## Verified Now

- What is currently working: the full loop from documents to a playable tree exists end to end for the static sample dataset. `apps/web/app/tree/page.tsx` fetches `GET {NEXT_PUBLIC_API_URL}/trees/{topic_id}`, renders the mastery tree via `@xyflow/react`, colors nodes by derived status (locked/unlocked/completed), and unlocks children live when a node is clicked-complete — verified visually via a real headless-browser session, not just typecheck. `apps/api`: `POST /graph/validate`, `assign_levels()`, `GET /trees/{topic_id}` (static sample). `packages/gpu-worker`: `POST /ingest`, `POST /embed`, `POST /build-graph`. `submit-quiz` still 501s (feat-008); no lesson/quiz/example generation yet (feat-007).
- What verification actually ran: `npm run lint` / `npm run build` in `apps/web` (both clean). `cd apps/api && python -m pytest tests/` — 11/11. `cd packages/gpu-worker && python -m pytest tests/` — 14/14 (regression check, unaffected by this frontend-only session). Additionally: started both `apps/api` and `apps/web` in the background, drove a real Chromium session (Playwright, installed temporarily then removed) against `/tree`, and visually confirmed correct rendering and the click-to-unlock interaction via screenshots, with zero browser console errors.

## Changed This Session

- Code or behavior added: `apps/web/app/tree/types.ts`, `unlock.ts`, `positions.ts` (renamed from `layout.ts`), `progressStore.ts`, `TreeNode.tsx`, `page.tsx` — the full skill-tree view.
- Infrastructure or harness changes: ran `npm install` in `apps/web` (411 packages; `next@14.2.5` has a known security advisory per npm's own warning — not addressed, flagging for a deliberate decision later rather than an incidental bump).
- Also fixed: a file named `app/tree/layout.ts` collides with Next.js App Router's reserved `layout.ts` convention — the build failed with a cryptic type error until renamed to `positions.ts`. Also fixed a terminology mismatch flagged in the previous handoff — `docs/concept-graph-pipeline.md` and `docs/brd.md` said a completed node's status is `"mastered"`, but `apps/web/tailwind.config.ts`'s actual color palette (`locked`/`unlocked`/`completed`) and the sample dataset both use `"completed"` — updated both docs (3 occurrences) to match the code, since the docs were the stale ones.
- Files modified: `apps/web/app/tree/*` (see above), `docs/concept-graph-pipeline.md`, `docs/brd.md`, `feature_list.json`, `progress.md`.

## Broken Or Unverified

- Known defect: none found in the new tree-view code.
- Unverified path: only manually tested against the static sample dataset (5 nodes) — not against a larger/denser tree that a real pipeline run might produce. The click-to-complete interaction is an intentional demo stand-in, not real quiz grading.
- Blockers for the next session: none.

## Next Session

- Highest-priority unfinished feature: feat-007, "Per-node lesson + quiz + real-world example (agentic RAG)" — lives in `apps/api`.
- Why it is next: feat-005 (its dependency) is passing; it can proceed in parallel with feat-006 conceptually, but feat-006 is now also done, so nothing blocks starting it.
- What counts as passing: for a given node, retrieve only that node's own source chunks (via the chunk_id/doc_id carried through since feat-001), call Fireworks to generate a lesson + MCQ quiz + real-world example, with a self-check that the quiz actually matches the lesson before returning it — scoped retrieval, not whole-corpus prompting. See docs/concept-graph-pipeline.md and docs/hackathon-scope.md §3 ("Agentic RAG for lesson & quiz generation").
- What must not change during that step: don't start feat-008's UI wiring (quiz submission, unlock-on-pass) in the same pass — feat-007 is generation-only; feat-008 consumes it. Note the click-to-complete stand-in in `apps/web/app/tree/page.tsx` will need to be replaced with a real quiz flow once feat-007+feat-008 land, not just extended.
- Recommended Next Step: add a service (e.g. `apps/api/app/services/teach.py`) with a Fireworks-backed `generate_lesson(node, source_chunks)` function, mirroring the local-vs-hosted client pattern already used in `packages/gpu-worker/worker/prerequisites.py`, plus a self-check step and tests using fakes (no live Fireworks key needed).

## Commands

- Startup: `./init.sh`
- Verification: see `CLAUDE.md` "Verification Commands"; per-feature checks live in `feature_list.json`.
- Focused debug command: `cd apps/web && npm run dev` then open `http://localhost:3000/tree` (needs `apps/api` running on port 8000 too — `cd apps/api && uvicorn app.main:app --reload --port 8000`). `cd apps/api && python -m pytest tests/ -v`; `cd packages/gpu-worker && python -m pytest tests/ -v`.
