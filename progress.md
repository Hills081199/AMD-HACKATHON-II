# Progress Log

## Current Verified State

- Last Updated: 2026-07-05
- Repository root: D:\AMD-HACKATHON-II
- Current Objective: Build the concept-dependency-graph pipeline end to end (feat-001 → feat-009 in `feature_list.json`). feat-001 through feat-007 are now passing; feat-008 (checkpoint quiz & unlock mechanic, in `apps/web`) is next.
- Standard startup path: `./init.sh`
- Standard verification path: see "Verification Commands" in `CLAUDE.md` — web lint/build, api/gpu-worker `compileall`, `cd apps/api && python -m pytest tests/` (16/16 passing), and `cd packages/gpu-worker && python -m pytest tests/` (14/14 passing).
- Highest-priority unfinished feature: feat-008, "Checkpoint quiz & unlock mechanic"
- Blockers: none currently. Day-1 risk flagged in `docs/hackathon-scope.md` §5: verify ROCm/PyTorch compatibility on the AMD Developer Cloud box before relying on it. feat-002/feat-003/feat-007 were verified with fakes (no live Gemma/Ollama server, model download, or Fireworks API key) — worth a real-infra pass once ROCm and Fireworks credentials are provisioned.
- Recommended Next Step: in `apps/web`, wire the node detail panel's quiz UI to `POST /trees/{topic_id}/nodes/{node_id}/submit-quiz` (currently a 501 stub in `apps/api/app/routers/trees.py`) — grade against the quiz's `pass_threshold`/`answer_index`, and on pass, mark the node `completed` in `progressStore.ts` so feat-006's existing unlock logic flips its children from locked to unlocked. Also note: feat-007's new `POST /trees/{topic_id}/nodes/{node_id}/lesson` endpoint expects the caller to supply the node's own chunks[] directly (no persisted chunk-text store exists yet) — worth reconciling with feat-009's pre-indexing pass, which will need to decide where chunk text lives long-term.

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

### Session 005

- Date: 2026-07-05
- Goal: Implement feat-004, "Self-checking graph agent (cycle/redundancy repair)."
- Completed: Added `apps/api/app/services/graph.py` — `build_graph` (candidate_edges[] → `networkx.DiGraph` with a `confidence` edge attribute), `repair_cycles` (bounded loop: on each iteration, find all cycles via `nx.simple_cycles()`, drop the lowest-confidence edge in the shortest one; after `max_iterations`, fall back to an unbounded while-loop that force-drops the weakest edge in any remaining cycle so the agent always terminates with a valid DAG), and `validate_graph` (orchestrates both, returns `{"edges": ..., "dropped_edges": [...]}` — the drop log with a `reason` per entry is what makes this auditable as an "agentic self-check" rather than a silent filter). Wired a new `POST /graph/validate` endpoint. This is `apps/api`'s first feature with real logic, so also set up its first test suite (`apps/api/tests/`, `apps/api/requirements-dev.txt`) and wired `pytest` into `init.sh`/`CLAUDE.md`.
- Verification run: `python -m compileall app tests` (pass); `python -m pytest tests/` in `apps/api` — 6/6 passed, including a test that specifically forces the force-drop fallback path (two independent 2-cycles, `max_iterations=1`, only 1 of the 2 needed drops fits the bounded budget) and confirms the result is still acyclic. Also re-ran `packages/gpu-worker`'s suite — 14/14, no regressions.
- Evidence captured: recorded in `feature_list.json` feat-004 `evidence[]`.
- Commits: not yet committed this session.
- Files or artifacts updated: `apps/api/app/services/__init__.py` (new), `apps/api/app/services/graph.py` (new), `apps/api/app/routers/graph.py` (new), `apps/api/app/main.py`, `apps/api/requirements-dev.txt` (new), `apps/api/tests/__init__.py` (new), `apps/api/tests/test_graph.py` (new), `apps/api/tests/test_graph_endpoint.py` (new), `init.sh`, `CLAUDE.md`, `feature_list.json`.
- Known risk or unresolved issue: `nx.simple_cycles()` is exponential in the worst case — fine for the hackathon's sparse, pre-filtered graphs, but worth watching if the real demo dataset ends up much larger/denser than expected. Not yet run on a real candidate-edge set from a live feat-003 run (Fireworks) — only synthetic edge lists in tests.
- Next best step: implement feat-005 (topological sort via `nx.topological_generations()`, tier assignment) in `apps/api`, and wire `GET /trees/{topic_id}` to return real data instead of its 501 stub.

### Session 006

- Date: 2026-07-05
- Goal: Implement feat-005, "Topological sort → tiered learning path."
- Completed: Added `apps/api/app/services/levels.py` — `assign_levels(edges, concepts)` builds a `DiGraph` seeded with every concept `id` (not just ones with an edge, so isolated concepts still get a node), groups via `nx.topological_generations()`, and returns `nodes[]` with `id`/`name`/`level`/`sources`/`status` (tier 0 = unlocked, everything else = locked). Wired `GET /trees/{topic_id}` in `apps/api/app/routers/trees.py` to serve `data/atlas_mastery_tree_sample.json` (path resolved from repo root, overridable via `SAMPLE_TREE_PATH`) instead of its `HTTPException(501)` — this was literally the file's own pre-existing TODO comment's recommendation, not a new call.
- Verification run: `python -m compileall app tests` (pass); `python -m pytest tests/` in `apps/api` — 11/11 passed (5 feat-004 + 6 feat-005, no regressions). Re-ran `packages/gpu-worker`'s suite — 14/14, no regressions.
- Evidence captured: recorded in `feature_list.json` feat-005 `evidence[]`, including a test that mirrors docs/concept-graph-pipeline.md's own sample tree (two branches converging) and directly asserts the DAG tier invariant, plus an endpoint test that re-checks that invariant against the real checked-in sample dataset (not just synthetic test data).
- Commits: not yet committed this session.
- Files or artifacts updated: `apps/api/app/services/levels.py` (new), `apps/api/app/routers/trees.py`, `apps/api/tests/test_levels.py` (new), `apps/api/tests/test_trees_endpoint.py` (new), `feature_list.json`, `progress.md`.
- Known risk or unresolved issue: `GET /trees/{topic_id}` is explicitly NOT wired to the live pipeline yet — it serves the static sample file regardless of `topic_id`; composing a real feat-002→feat-005 run into this endpoint is a bigger integration task, likely alongside feat-009. `data/` isn't copied into the Docker image (`docker/api.Dockerfile` only `COPY`s `apps/api/`) — `SAMPLE_TREE_PATH` is the escape hatch, not yet used. Also noticed while reading the sample dataset: it uses `"completed"` for a mastered node's status, while `docs/concept-graph-pipeline.md`'s schema says `"mastered"` — a naming mismatch to reconcile when feat-006/008 build the real unlock mechanic.
- Next best step: implement feat-006 (skill-tree UI with unlock logic) in `apps/web`, replacing the `TODO: render mastery tree` placeholder in `app/tree/page.tsx`. Requires `npm install` in `apps/web` first (node_modules still not installed as of this session).

### Session 007

- Date: 2026-07-05
- Goal: `npm install` in `apps/web`, then implement feat-006, "Skill-tree UI with unlock logic."
- Completed: Ran `npm install` in `apps/web` (411 packages; flagged a known `next@14.2.5` security advisory — not addressed, out of scope, noted for awareness rather than silently upgraded). Confirmed baseline lint/build passed on the pre-existing placeholder pages before touching anything. Implemented the tree view across `apps/web/app/tree/`: `types.ts` (shared shapes), `unlock.ts` (derives locked/unlocked/completed status from a single source of truth — a completed-id set — plus edge structure, rather than trusting a possibly-stale `status` field), `positions.ts` (layout into columns by level), `progressStore.ts` (zustand store holding `completedIds` client-side so unlocks react without a page reload), `TreeNode.tsx` (custom React Flow node, colored via the `locked`/`unlocked`/`completed` colors already defined in `tailwind.config.ts`), and `page.tsx` (fetches `GET {NEXT_PUBLIC_API_URL}/trees/{topic_id}`, renders via `@xyflow/react`).
- Verification run: `npm run lint` (clean) and `npm run build` (compiled + type-checked) — the build caught a real bug: a file named `layout.ts` collides with Next.js App Router's reserved filename inside `app/`, renamed to `positions.ts` to fix. Beyond typecheck/build, actually ran the app: started `apps/api` (uvicorn) and `apps/web` (`next dev`) in the background, installed Playwright temporarily, and drove a real headless-Chromium session against `/tree`. Confirmed visually (screenshots inspected): tier-0 completed nodes render green, the unlocked node renders blue, locked nodes render grey, grouped into columns by level; clicking the unlocked "Loss Functions" node turned it green and immediately flipped its child "Gradient Descent" from grey/locked to blue/unlocked with no page reload and no browser console errors, while the further "Neural Networks" node correctly stayed locked. Re-ran `apps/api` (11/11) and `packages/gpu-worker` (14/14) test suites afterward — no regressions from this frontend-only change. Cleaned up: killed both background dev servers, removed the temporary Playwright install.
- Evidence captured: recorded in `feature_list.json` feat-006 `evidence[]`, including the screenshot-based manual verification (not just typecheck) and the layout.ts naming-collision bug found and fixed along the way.
- Commits: not yet committed this session.
- Files or artifacts updated: `apps/web/app/tree/{types.ts, unlock.ts, positions.ts, progressStore.ts, TreeNode.tsx, page.tsx}` (new/replaced), `feature_list.json`, `progress.md`. Also fixed the `mastered`→`completed` terminology mismatch flagged in the previous session's handoff: updated `docs/concept-graph-pipeline.md` and `docs/brd.md` (3 occurrences total) to say `completed`, matching `tailwind.config.ts`'s actual color names and the sample dataset — the doc wording was the stale one.
- Known risk or unresolved issue: the click-to-complete interaction is a demo-only stand-in for feat-008's real checkpoint-quiz submission (any click on an unlocked node "passes" it instantly, no quiz UI yet). `next@14.2.5` has a known security advisory per `npm install`'s own warning — not upgraded, flagging for awareness since a version bump could be a breaking change worth doing deliberately, not incidentally.
- Next best step: implement feat-007 (per-node lesson/quiz/example via agentic RAG) in `apps/api` — this is what feat-008's real quiz UI will eventually call into.

### Session 008

- Date: 2026-07-05
- Goal: Implement feat-007, "Per-node lesson + quiz + real-world example (agentic RAG)."
- Completed: Added `apps/api/app/services/teach.py` — `FireworksClient` (hosted chat-completions client, separate instance from gpu-worker's step-4 `FireworksClient` since the two services deploy independently) with `generate()` (lesson + MCQ quiz + real-world example, prompted only with the given chunks' excerpts) and `check_alignment()` (the self-check: does the quiz actually test the lesson's content, and is the marked answer correct), and `generate_lesson_package()` — a bounded retry loop (default 2 attempts) that regenerates the whole package on a failed alignment check and, if every attempt still fails, returns the last attempt flagged with `self_check.passed = False` instead of raising (so a stubborn misalignment degrades gracefully in a demo rather than 500ing). Wired `POST /trees/{topic_id}/nodes/{node_id}/lesson` in `apps/api/app/routers/teach.py` via `Depends(get_fireworks_client)`, same override pattern as gpu-worker's `/embed`/`/build-graph`.
- Verification run: `python -m compileall app tests` (pass); `python -m pytest tests/` in `apps/api` — 16/16 passed (11 pre-existing + 5 new, no regressions), including a forced-mismatch test proving the self-check guard actually triggers a second `generate()` call (not just a re-check) and a forced-always-fail test proving the function still returns a result rather than raising. Re-ran `packages/gpu-worker` — 14/14, no regressions. Full `./init.sh` (web lint/build + both python suites) — all green.
- Evidence captured: recorded in `feature_list.json` feat-007 `evidence[]`.
- Commits: not yet committed this session.
- Files or artifacts updated: `apps/api/app/services/teach.py` (new), `apps/api/app/routers/teach.py` (new), `apps/api/app/main.py`, `apps/api/tests/test_teach.py` (new), `apps/api/tests/test_teach_endpoint.py` (new), `feature_list.json`, `progress.md`.
- Known risk or unresolved issue: apps/api has no persisted chunk-text store — chunks only ever existed ephemerally inside a single gpu-worker `/ingest`→`/embed` request, and `docs/hackathon-scope.md` §5's SQLite/JSON storage line item hasn't been built as its own feature. Rather than inventing a store as a side effect of this feature, the new endpoint takes the node's chunks[] directly in the request body — scoping to "this node's own sources only" is enforced by the request shape, not by a filter over a larger store. This needs to be reconciled with feat-009 (pre-indexed demo dataset), which will need to decide where chunk text is persisted long-term so the real `/trees/{topic_id}` flow can supply it. Not verified against a live Fireworks API — `FireworksClient` is only verified against a fake in tests.
- Next best step: implement feat-008 (checkpoint quiz & unlock mechanic) in `apps/web`, wiring the quiz UI to `POST /trees/{topic_id}/nodes/{node_id}/submit-quiz` (currently a 501 stub) and reusing feat-006's existing `progressStore`/unlock logic on a pass.
