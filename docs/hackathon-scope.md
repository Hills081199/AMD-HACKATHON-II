# Atlas — 7-Day Hackathon Scope Review & Feature Prioritization

_Product Owner Assessment · AMD Developer Hackathon, Track 3 (Unicorn)_

For the product pitch and business context, see [`brd.md`](brd.md). For the
technical detail behind the graph pipeline referenced throughout this doc,
see [`concept-graph-pipeline.md`](concept-graph-pipeline.md).

## 1. Product Owner Assessment

The core idea is genuinely strong for this competition: a concept-dependency graph, computed with a topological sort and rendered as an unlockable skill tree, is a real technical problem, it's visually demoable in under two minutes, and it clearly differentiates Atlas from "upload a PDF, get a chatbot" clones. The AMD GPU / Fireworks split (heavy batched embedding and clustering on ROCm, reasoning on Fireworks) is also the right shape for the platform-usage judging criterion.

The risk is not the core - it's the roadmap. The original product brief (see `brd.md`) also specs spaced repetition, audio/video overviews, gamification, adaptive quizzes, dashboards, personalization, and collaboration - a full v2 product plan. None of it can be built to a polished standard in 7 days, and attempting slices of all of it is the most common way hackathon teams end up with an incomplete, unpolished demo - which is directly punished by the "completeness/polish" criterion. My recommendation is to cut all of it from the build and keep it only as a single "what's next" slide for the market-potential story.

Second, the current architecture reads as a linear pipeline (extract → build graph → sort → generate) rather than something "agentic." Since this is an AI hackathon, I'd reframe and lightly extend three pipeline stages into agent loops - self-checking, scoped retrieval, autonomous tool use - which costs very little extra engineering (the data is already there) but meaningfully strengthens both the "creativity/originality" score and the entry's fit with an AI/agentic-RAG theme.

## 2. What to Cut (and why)

| **Feature (from the original brief)**                  | **Why it should be cut for a 7-day build**                                                                                       |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Spaced repetition (SM-2 scheduling)                | Depends on multi-session return data judges will never see live; no payoff inside a 2-minute demo.                               |
| Audio overview / 2-voice podcast per node          | Requires a TTS + dialogue-scripting pipeline on top of everything else; high effort, doesn't reinforce the graph differentiator. |
| Auto-generated video / slide summaries             | Video generation infra is heavy and slow; furthest feature from the core technical moat.                                         |
| Gamification (XP, badges, streaks, leaderboards)   | Only feels real with persistent multi-day usage and accounts; in a live demo it's an empty progress bar.                         |
| Adaptive quiz difficulty + multiple question types | Polish feature. A single MCQ checkpoint is enough to prove the "pass to unlock" mechanic.                                        |
| Dashboard, knowledge heatmap, PDF/Notion export    | A reporting layer with no bearing on the on-stage "wow" moment; adds UI surface, not judging leverage.                           |
| Collaborative / multi-user skill tree              | Needs auth, roles, and real-time sync - infrastructure cost is too high relative to the win condition.                           |
| Personalization by learning style                  | Not objectively demonstrable live in 2 minutes; hard to prove it's actually working.                                             |
| Public learning tracks (publish/clone)             | Needs accounts, moderation, and a sharing/licensing policy - none of which is needed to prove the graph differentiator.          |

## 3. What to Add - Lightweight Agentic AI Upgrades

These four additions replace essentially everything cut above, at a fraction of the cost, because they reuse chunks, embeddings, and Fireworks calls the pipeline already needs. They also make the entry visibly agentic rather than "a script that calls an LLM four times."

| **Addition**                             | **What it does**                                                                                                                                                                  | **Why it's worth it**                                                                                                                               |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Self-checking graph agent                | After building the dependency graph, an agent loop re-checks it for cycles or redundant edges and repairs before the topological sort runs.                                       | Turns "we called an LLM" into "our agent validates its own output" - strong originality and platform-usage signal, reuses existing Fireworks calls. |
| Agentic RAG for lesson & quiz generation | Per node, retrieve only the relevant chunks (not the whole corpus), cite the source, and have the agent self-check that the quiz actually matches the lesson before returning it. | This is literally Agentic RAG done properly - better and cheaper than naive whole-corpus prompting, and it's the theme judges are looking for.      |
| One-shot gap-filling agent               | If a node lacks enough supporting text, one autonomous action: search the web, pull a single supporting snippet, cite it.                                                         | Visible, low-risk autonomous tool-use moment on stage; a cheap stand-in for the cut "suggest more material" and personalization features.           |
| Per-node tutor chat (RAG Q&A)            | A lightweight chat scoped to that node's source chunks only, so a judge can ask a follow-up question live.                                                                        | Reuses the same retrieval stack; gives an interactive demo moment without building audio/video overview.                                            |

## 4. Consolidated Feature Table (7-Day Build)

_Priority key: P0 = must ship for the demo path to work at all. P1 = build only if the schedule holds. P2 = explicitly cut from the build; keep as a single roadmap slide only._

### P0 - Core demo path

| **Feature**                                               | **AI / Agentic Component**     | **Runs on**                | **Day** |
| --------------------------------------------------------- | ------------------------------ | -------------------------- | ------- |
| Document ingest & chunking                                | -                              | Cloud                      | 1       |
| Embedding + concept extraction & clustering (Gemma bonus) | Embedding model, Gemma tagging | AMD GPU / ROCm             | 1-2     |
| Dependency-graph construction (prerequisite edges)        | Fireworks reasoning            | AMD GPU / ROCm + Fireworks | 2-3     |
| Self-checking graph agent (cycle/redundancy repair)       | Agentic validation loop        | Fireworks                  | 3       |
| Topological sort → learning path                          | -                              | Cloud (light)              | 3       |
| Skill-tree UI with unlock logic                           | -                              | React / Cloud              | 3-4     |
| Per-node lesson + quiz + real-world example (Agentic RAG) | Scoped retrieval + self-check  | Fireworks                  | 4-5     |
| Checkpoint quiz & unlock mechanic (MCQ only)              | Fireworks                      | Fireworks / React          | 5       |
| Pre-indexed, deterministic demo dataset                   | -                              | -                          | 5-6     |

### P1 - Stretch, only if schedule holds

| **Feature**                                             | **AI / Agentic Component** | **Runs on**            | **Day** |
| ------------------------------------------------------- | -------------------------- | ---------------------- | ------- |
| Gap-filling agent (one web search call per weak node)   | Tool-using agent           | Fireworks + web search | 6       |
| Per-node tutor chat (RAG Q&A)                           | Scoped retrieval agent     | Fireworks              | 6       |
| "Replay path" linear summary view (text only, no audio) | -                          | React                  | 6       |

### P2 - Cut from build, roadmap slide only

| **Feature**                                                                                                                                        | **Where it lives instead**                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Spaced repetition, audio/video overview, gamification suite, dashboard & heatmap, PDF/Notion export, collaboration, learning-style personalization, public learning tracks | Single "what's next" slide in the pitch deck, and the Post-MVP Roadmap section of `brd.md`, to support the product/market-potential score without consuming build time. |

## 5. Technology Stack by Layer

| **Layer**                                     | **Tasks**                                         | **Recommended Technology**                                                                                                             | **Why This Choice**                                                                                                                                                           |
| --------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ingest**                                    | Read PDF/PPTX/DOCX files, split into chunks       | **PyMuPDF/pdfplumber** (PDF), **python-pptx**, or **unstructured.io**                                                                  | Supports multiple document formats efficiently without writing custom parsers for each file type.                                                                             |
| **Understand - Embedding**                    | Convert content into vector embeddings            | Open-source **Sentence Transformers** (e.g., **bge-large**, **e5-large**) running on **PyTorch ROCm**                                  | Runs on AMD GPUs, requires no licensing, and provides excellent quality for small-to-medium document collections.                                                             |
| **Understand - Concept Extraction / Tagging** | Identify learning concepts                        | **Gemma (2B/7B)** served locally via **vLLM-ROCm** or **Ollama**, on the AMD GPU                                                       | Meets the "Best Use of Gemma" bonus requirement while running entirely on-premises without API costs - and is the piece of the stack that puts actual LLM inference on AMD hardware, not just embeddings. |
| **Understand - Clustering**                   | Merge duplicate or highly similar concepts        | **scikit-learn** (KMeans/HDBSCAN) or graph community detection (**networkx/igraph**, Louvain/Leiden) on the embedding similarity graph | Lightweight, fast, and easy to debug within a hackathon timeframe.                                                                                                            |
| **Structure - Prerequisite Inference**        | Infer prerequisite relationships (A → B)          | **Fireworks API** (Llama 3.x or equivalent), querying only candidate pairs filtered by cosine similarity and co-occurrence             | Avoids expensive O(n²) LLM calls across every concept pair, significantly reducing latency and cost.                                                                          |
| **Structure - Graph Object & Validation**     | Store and validate the prerequisite graph         | **networkx** (Python) with built-in cycle detection and topological sorting                                                            | Eliminates the need to implement graph algorithms from scratch.                                                                                                               |
| **Structure - Self-Checking Agent**           | Iteratively repair graph inconsistencies          | Lightweight Python orchestration (async functions + bounded retry loop) without heavy agent frameworks                                 | Frameworks like LangGraph or CrewAI require additional learning time; a custom loop is simpler and easier to debug during a 7-day hackathon.                                  |
| **Order**                                     | Topological sorting                               | **networkx.topological_sort**                                                                                                          | Built-in, reliable, and executes instantly.                                                                                                                                   |
| **Teach**                                     | Generate lessons, quizzes, and examples using RAG | **Fireworks API** with cosine-similarity retrieval over existing embeddings (no dedicated vector database required)                    | For a corpus of 10-30 documents, in-memory **NumPy** or **FAISS** retrieval is sufficient without deploying Pinecone or Weaviate.                                             |
| **Backend API**                               | Orchestrate the entire pipeline                   | **FastAPI** (Python), background tasks, polling-based job status                                                                       | Excellent async support, rapid REST API development, and straightforward GPU worker integration.                                                                              |
| **Play - Frontend**                           | Interactive skill tree interface                  | **Next.js + TypeScript + React Flow + Tailwind CSS**                                                                                     | React Flow provides built-in node graph visualization, zooming, panning, and drag-and-drop, saving substantial development time compared to implementing D3/SVG from scratch. Next.js is the framework actually scaffolded in `apps/web`. |
| **Storage**                                   | Store documents, graphs, and processing results   | **SQLite** and JSON files                                                                                                              | Keeps the demo simple without requiring PostgreSQL or multi-session infrastructure.                                                                                           |
| **Infrastructure**                            | Containerization (required for submission)        | **Docker + Docker Compose**, with separate containers for frontend, backend, and GPU worker (using **rocm/pytorch** base image)        | Satisfies submission requirements while clearly demonstrating AMD GPU utilization.                                                                                            |

### Important Technical Note

**Verify ROCm compatibility on Day 1.** This is often the biggest blocker in AMD GPU hackathons due to driver versions, PyTorch-ROCm compatibility, and library support. Discovering issues early leaves six days to recover; discovering them late can jeopardize the entire competition.

## 6. Seven-Day Sprint Plan

**Assumption:** A team of four:

- **Backend/Infrastructure Engineer** (GPU pipeline)
- **AI/Prompt Engineer** (LLM orchestration & agent)
- **Frontend Engineer**
- **PM/Designer** (dataset, presentation, demo video)

Adjust responsibilities if your team size differs.

| **Day**   | **Backend / Infrastructure**                                                                                                                          | **AI / Prompt Engineering**                                                                           | **Frontend**                                                                               | **PM / Design**                                                                          |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| **Day 1** | Set up repository, Docker skeleton, ROCm base image, initialize FastAPI, test Fireworks API connectivity                                              | Select embedding model, design concept extraction prompts, test on one sample document                | Scaffold Next.js + Tailwind + React Flow, build a mock skill tree using JSON                 | Finalize demo dataset (10-30 documents focused on one domain), outline the project pitch |
| **Day 2** | Build end-to-end ingest and chunking pipeline, compute embeddings on the GPU                                                                          | Implement concept extraction and clustering to merge duplicate concepts                               | Connect UI to a mock API returning graph JSON, create lock/unlock node components          | Evaluate chunk quality using the demo dataset                                            |
| **Day 3** | Call Fireworks API to infer prerequisite edges, construct the graph using NetworkX                                                                    | Implement the self-checking agent (cycle detection, repair, topological sort)                         | Render the actual graph as an interactive skill tree and stub unlocking logic              | Run the full ingest → graph pipeline on the demo dataset and identify issues early       |
| **Day 4** | Build APIs for lesson, quiz, and example generation using node-scoped RAG                                                                             | Design structured JSON prompt templates for lessons, quizzes, and examples; validate quiz consistency | Develop node detail panels (lesson, quiz UI), unlock subsequent nodes upon quiz completion | Start preparing the pitch deck and demo script                                           |
| **Day 5** | **Integration Day:** connect the complete pipeline to the demo dataset and pre-cache all outputs to avoid live LLM dependency during the presentation | Debug and refine prompts collaboratively                                                              | Bug fixing, loading states, UI polish                                                      | Finalize the storytelling narrative and prepare a backup demo recording                  |
| **Day 6** | Buffer day; optionally implement a gap-filling agent or node-level tutor chat                                                                         | Develop stretch features if time permits                                                              | Polish UI and animations                                                                   | Record the demo video and rehearse the presentation                                      |
| **Day 7** | Final submission checklist (repository, README, Docker containers, cover image, tags, deployment URL), final bug fixes                                | Final validation                                                                                      | Final polishing                                                                             | Final rehearsal, complete the demo video and presentation slides                         |

## 7. Judging-Criteria Alignment

| **Criterion**              | **How the scoped plan addresses it**                                                                                                                                                    |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Creativity / originality   | Dependency graph + self-checking agent loop, framed explicitly as agentic RAG rather than a single-shot pipeline.                                                                       |
| Completeness / polish      | Narrow P0 scope with a pre-indexed, deterministic dataset removes the main live-demo failure point.                                                                                     |
| AMD platform usage         | Heavy, batched work (embeddings, clustering, graph construction, Gemma tagging) on ROCm; reasoning and agent loops on Fireworks - a genuine hybrid split, not a single remote API call. |
| Product / market potential | Core loop targets a real recurring need (students, self-learners, researchers); the cut roadmap is preserved as a forward-looking slide rather than half-built in the product.          |
