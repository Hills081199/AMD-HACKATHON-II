**ATLAS**

**_"Learn anything you read,_**

**_the fun way."_**

**Business Requirement Document**

Hanoi, July 2026

# **I. Introduction**

## **1. Overview**

### **1.1 Project Information**

- Project name: Atlas
- Project code: ATL-2026-01
- Software type: Web Application
- Hackathon: AMD Developer Hackathon: ACT II
- Track: Track 3 - Unicorn Track (All Levels)
- Kickoff: Monday, 6 July 2026, 22:00 ICT
- Prize Pool: \$20,000+

### **1.2 Project Team**

| **Full Name**    | **Role** | **Email** | **Mobile** |
| ---------------- | -------- | --------- | ---------- |
| Hoang Nguyen Van | PO       |           |            |
|                  |          |           |            |
|                  |          |           |            |
|                  |          |           |            |
|                  |          |           |            |

## **2. Product Background**

Learners (students, self-learners, researchers) don't lack material - they
often have dozens of PDFs, slides, and papers but no idea what order to read
them in. Read them in the wrong order and you hit a concept you don't
understand yet, stall, and lose motivation. Existing AI tools (summarizers,
RAG chatbots that answer questions about documents, quiz generators) only
answer questions about the content - none of them actually build the route
through it.

Atlas is an AI-first learning platform that solves this directly: a user
drags in a messy pile of documents, and the system reads them, identifies the
**concepts** inside, and infers which concepts must be learned before others
(e.g., you need to understand "derivatives" before "gradient descent"). From
this network of relationships - a **concept-dependency graph** - the system
runs a **topological sort** to compute the optimal learning order: no
skipping ahead, no getting lost. This order is displayed as a **skill tree**,
like in a video game: each concept is a node, and a node only unlocks once
you pass the checkpoint quiz for the previous one. Every node comes with a
short lesson, a quiz, and a real-world example, so it's not just theory.

The defensible "moat" isn't a chatbot or a summarizer (anyone can build
those) - it's the real technical problem: building the graph and computing
the optimal path through it. It's a genuine engineering challenge, it's
visual, and it makes for a strong 2-minute demo (drag in documents → skill
tree appears instantly). See [`hackathon-scope.md`](hackathon-scope.md) §1
for the full product-owner rationale, and
[`concept-graph-pipeline.md`](concept-graph-pipeline.md) for how the graph is
actually built.

Longer-term, Atlas can layer in Duolingo-style engagement mechanics (streaks,
XP, spaced repetition) on top of this core loop - see §7.1b, "Post-MVP
Roadmap," for that full feature set, which is explicitly out of scope for the
hackathon build.

### **2.1 Clarifying Questions**

- Who is the primary target audience — self-learners, students, or
  professionals in continuing education? **Open.** The rest of this document
  uses "self-learners, students, and researchers" (§2, §5) and, separately,
  "self-learners plus K-12, higher-ed, and corporate L&D" (§4.3) somewhat
  interchangeably — needs a single, deliberate answer before go-to-market
  positioning is finalized.
- Which document formats must be supported at launch (PDF, EPUB, DOCX, TXT,
  web URL)? **Resolved for the hackathon MVP:** the ingest pipeline supports
  PDF/PPTX/DOCX (see [`hackathon-scope.md`](hackathon-scope.md) §5,
  "Ingest" row). EPUB, plain TXT, and web-URL ingestion are not built for the
  MVP; treat them as post-MVP format support.
- Which LLM providers will Atlas integrate with (OpenAI, Anthropic, local
  models via Ollama)? **Resolved:** Gemma (2B/7B), served locally via
  vLLM-ROCm/Ollama on the AMD GPU, for concept extraction; Fireworks AI
  (Llama 3.x) for prerequisite inference and lesson/quiz generation. No
  OpenAI or Anthropic integration is planned. See §7.3 and
  [`concept-graph-pipeline.md`](concept-graph-pipeline.md).
- How will user progress and spaced-repetition state be persisted across
  sessions and devices? **Resolved for the hackathon MVP:** there is no
  multi-user account system or cross-device sync in the MVP (see §7.1b) —
  node status (`locked`/`unlocked`/`completed`) is held in local/session
  state against the single pre-indexed demo dataset. Durable, cross-device
  progress persistence is a post-MVP concern, to be designed alongside user
  accounts.
- Will learning tracks be shareable between users, and if so, under what
  license? **Open.** Public/shareable learning tracks are cut from the
  hackathon MVP (§7.1b), and no sharing/licensing model has been designed
  yet.
- What is the maximum document size and number of concurrent uploads per
  user? **Resolved:** see §7.2 - 20 MB per document, 10 documents per user
  during the MVP.

## **3. Existing Systems**

Atlas's technical differentiation from all three systems below is the
concept-dependency graph and skill tree (§2) - none of them compute or
visualize prerequisite order between concepts, they only generate flat sets
of study material.

### **3.1 Quizlet <https://quizlet.com/>**

**Description:** A large-scale study platform where users upload notes or textbooks and Quizlet's Magic Notes AI generates flashcards, practice tests, and study guides. Gamification includes streaks, achievements, and modes such as Learn, Match, and Blast to drive engagement.

**Pros:** Massive installed user base among students; mature AI-powered content generation from user material; well-established gamification loop; strong brand recognition; broad content library seeded by community.

**Cons:** Aggressive paywalls on the most useful AI features; primarily K-12 and undergraduate focus; closed-source; not tuned for long-form professional or research documents; shallow adaptive spaced repetition compared to dedicated tools.

### **3.2 StudyFetch <https://www.studyfetch.com/>**

**Description:** An AI study assistant that ingests uploaded PDFs, slides, and lecture notes to generate flashcards, quizzes, and an interactive AI tutor (Spark.E). Includes gamified elements such as study streaks and progress tracking.

**Pros:** Purpose-built around document ingestion plus AI study material generation; unifies summary, quiz, flashcard, and chat modalities in a single flow; explicit gamification for daily engagement.

**Cons:** Closed-source and subscription-gated; smaller community and content library than Quizlet or Anki; limited transparency on model provenance; no open ecosystem for user-contributed learning tracks.

### **3.3 RemNote <https://www.remnote.com/>**

**Description:** A note-taking and knowledge-management app that combines Markdown-style notes with inline spaced-repetition flashcards and an AI copilot for Q&A and card generation from imported documents.

**Pros:** Deeply integrates learning with knowledge capture; strong spaced-repetition engine (FSRS); growing AI feature set for document understanding; loyal power-user community.

**Cons:** Steep learning curve; positioned as productivity rather than habit-forming, so gamification is minimal; core AI features gated behind paid tier; closed-source core.

## **4. Business Opportunity: Hackathon MVP**

Atlas is submitted to the AMD Developer Hackathon: ACT II under the Unicorn Track, where projects are judged on creativity, originality, completeness, use of AMD platforms, and product/market potential rather than benchmark performance. The MVP validates the core hypothesis: that self-learners will engage with an open-source tool that turns their own reading material into an optimally-ordered, playable skill tree. Incumbents such as Quizlet, StudyFetch, and RemNote each solve a slice of this problem, but all are closed-source, gated behind paywalls, and none compute a prerequisite-ordered path through the material; Atlas differentiates first on the concept-dependency graph itself, and second on being open-source and extensible.

### **4.1 Hackathon Context**

- Event: AMD Developer Hackathon: ACT II, a hands-on cloud-based event for developers, founders, and engineers building AI agents and high-performance AI applications on AMD GPUs.
- Kickoff: Monday, 6 July 2026, 22:00 ICT (Indochina Time).
- Prize pool: \$20,000+, with additional recognition on AMD social channels and at AMD developer events.
- Infrastructure: AMD Developer Cloud (AMD GPUs), ROCm open-source GPU stack, and Fireworks AI API for hosted model access. All submissions must be containerized.
- Credits: \$50 in Fireworks AI API credits for all participants; new AMD AI Developer Program members additionally receive \$100 in AMD Developer Cloud credits and a one-month DeepLearning.AI Pro membership.

### **4.2 Monetization Models**

Not part of the hackathon MVP build (see §7.1b) - captured here as the
forward-looking business model for the pitch deck:

- Freemium: Core features free; paid tier unlocks unlimited uploads, premium AI models, and advanced analytics.
- Pay-per-use credits: Users purchase credits for AI-generated quizzes, flashcards, and summaries at scale.
- Institutional licensing: B2B plans for schools, universities, and corporate L&D teams with SSO and admin controls.
- Community-supported: Open-source core with optional sponsorships, GitHub Sponsors, and enterprise support contracts.

### **4.3 Path to Winning the Unicorn Track**

The Unicorn Track is scored on five criteria: creativity, originality, completeness, use of AMD platforms, and product/market potential. Atlas has no benchmark to beat, so every design and demo decision must map back to one of these five. The plan below anchors each criterion to a concrete move.

**Creativity:** Frame Atlas as an emotional promise, not a feature list. The demo's hero moment is a user dragging in a real book and watching a skill tree materialize instantly, followed by unlocking the first node with a checkpoint quiz - a payoff none of the three incumbents delivers on the user's own material.

**Originality:** The concept-dependency graph and self-checking agent are the primary technical moat - none of the incumbents in §3 compute or visualize prerequisite order. Open-source is the secondary, business-model-level differentiator: every competitor in §3 is closed and paywalled, and Atlas ships under an OSI-approved license (MIT - see [`LICENSE`](../LICENSE)) with self-hosting instructions.

**Completeness:** A shallow but end-to-end demo beats a deep but partial one. The MVP must show the full loop - upload, parse, build graph, play, track progress - even if each layer is minimal. Scope discipline in §7.1/§7.2 and [`hackathon-scope.md`](hackathon-scope.md) protects this outcome.

**Use of AMD Platforms:** Non-trivial workload on AMD hardware. Embedding generation and Gemma-based concept extraction run locally on AMD Developer Cloud GPUs via ROCm - this is the piece of the stack that puts actual LLM inference on AMD hardware, not just embeddings. The containerized submission reproduces cleanly on the judges' standardized environment. Gemma served locally targets the Best Use of Gemma Models challenge for additional recognition.

**Product/Market Potential:** Close the pitch with a defined TAM (self-learners plus K-12, higher-ed, and corporate L&D), the monetization ladder from §4.2, and a differentiation matrix versus Quizlet, StudyFetch, and RemNote. Judges should leave convinced Atlas is a startup with a working demo, not a hackathon prototype.

## **5. Software Product Vision**

For self-learners, students, and lifelong readers who don't know what order
to study their own material in, Atlas is an open-source learning platform
that turns any pile of documents into a concept-dependency graph and an
unlockable skill tree - each node backed by a short lesson, a checkpoint
quiz, and a real-world example, cited back to its source. Unlike NotebookLM,
which answers questions but never tells you what to read next, or Duolingo,
which is locked to language learning, Atlas computes the actual optimal path
through material you bring yourself. Duolingo-style engagement mechanics
(streaks, XP, spaced repetition) are a natural extension of this loop and are
tracked as post-MVP roadmap items (§7.1b), not part of the initial mechanic.

## **6. System Actors**

| **#** | **Actor**       | **Description**                                                                                                                               | **MVP status** |
| ----- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| **1** | Learner         | End user who uploads documents and completes the generated skill tree: lessons, checkpoint quizzes, and unlock progression.                   | Active         |
| **2** | AI Service      | Gemma (local, on the AMD GPU via ROCm) for embeddings and concept extraction; Fireworks AI (Llama 3.x) for prerequisite inference, lesson/quiz/example generation, and the self-checking graph agent. | Active         |
| **3** | Content Creator | User who curates and publishes public learning tracks based on a document set, making them discoverable to other learners.                    | Post-MVP (§7.1b) |
| **4** | Administrator   | Manages platform operations: user accounts, content moderation, feature flags, and system-wide configuration.                                 | Post-MVP (§7.1b) |

## **7. Project Scope & Limitations**

### **7.1 Major Features (Hackathon MVP)**

- Document Upload & Parsing: Users upload PDF, PPTX, or DOCX files; the
  ingest pipeline extracts and chunks the content by heading/slide boundary.
- Concept-Dependency Graph: Embeddings + Gemma-based concept extraction,
  clustering/dedupe, Fireworks-based prerequisite inference, and a
  self-checking agent that repairs cycles before the graph is finalized.
  See [`concept-graph-pipeline.md`](concept-graph-pipeline.md).
- Optimal Learning Order: `networkx.topological_generations()` groups the
  validated graph into tiers, allowing parallel branches rather than one
  straight line.
- Skill-Tree UI with Unlock Logic: Each concept is a node; a node unlocks
  once every prerequisite node is `completed`.
- Per-Node Lesson, Quiz & Real-World Example (Agentic RAG): Scoped retrieval
  over that node's source chunks only, with a self-check that the quiz
  matches the lesson before it's shown.
- Checkpoint Quiz & Unlock Mechanic (MCQ only): Passing a node's quiz marks
  it `completed` and unlocks its children.
- Pre-Indexed, Deterministic Demo Dataset: The full pipeline is run ahead of
  time on the chosen document set so the live demo doesn't depend on
  Fireworks' latency or reliability.
- Containerized Deployment: The full stack (frontend, API, GPU worker) ships
  as Docker containers with a single-command bring-up via
  `docker-compose.yml`.

### **7.1b Post-MVP Roadmap (explicitly cut from the hackathon build)**

The following were in the original product concept but are deliberately out
of scope for the 7-day build - see
[`hackathon-scope.md`](hackathon-scope.md) §2 and §4 for the full
cut rationale and where each item goes in the pitch deck instead:

- Gamified Learning Loop (XP, streaks, hearts, daily goals)
- Spaced-Repetition Review Engine (SM-2/FSRS scheduling)
- AI-Generated Flashcards (as a standalone modality alongside the skill tree)
- Progress Dashboard, knowledge heatmap, PDF/Notion export
- Public Learning Tracks (publish/clone) and Content Creator / Administrator
  actor roles
- User Authentication & Profile, cross-device progress persistence
- Collaborative / multi-user skill tree
- Personalization by learning style
- Payment/billing integration (monetization models in §4.2 are stubbed only)

### **7.2 Limitations & Exclusions**

- Web application only; native iOS and Android apps are out of scope for the MVP.
- English-language documents only at launch; multi-language support is post-MVP.
- No offline mode; an active internet connection is required.
- No collaborative or group study features (shared sessions, live study rooms) in the MVP.
- No payment or billing integration; monetization tiers are stubbed for post-MVP.
- Maximum upload size of 20 MB per document and 10 documents per user during the MVP.
- No mobile-optimized responsive polish beyond a functional layout.

### **7.3 Technology Stack**

- Compute: AMD Developer Cloud with AMD GPUs, accessed via ROCm, used for
  embedding generation and local Gemma inference (concept extraction).
- Model access: Gemma (2B/7B) served locally via vLLM-ROCm/Ollama on the AMD
  GPU for concept extraction (eligible for the Best Use of Gemma Models
  challenge); Fireworks AI (Llama 3.x) for prerequisite inference and
  lesson/quiz/example generation.
- Backend: Python (FastAPI) service exposing document ingestion, graph
  construction, and quiz/unlock endpoints.
- Storage: SQLite and JSON files, with in-memory NumPy/FAISS for embedding
  retrieval - sufficient for a 10-30 document corpus and a single demo
  session, without standing up PostgreSQL/pgvector or a dedicated vector
  database. Revisit Postgres + pgvector only if multi-user accounts or a much
  larger corpus become in-scope post-MVP.
- Frontend: Next.js + TypeScript + React Flow + Tailwind CSS (`apps/web`).
- Deployment: All components packaged as Docker containers and orchestrated
  via `docker-compose`, satisfying the hackathon's containerization
  requirement.

See [`hackathon-scope.md`](hackathon-scope.md) §5 for the full per-layer
technology table and rationale.

# **II. Concerns & Open Questions**

- LLM cost per active user is unknown; heavy quiz/lesson generation could
  make a future freemium tier unsustainable without careful caching and
  prompt design.
- Content-quality risk: AI-generated lessons/quizzes may hallucinate or
  misrepresent source material, which erodes learner trust.
- Copyright and fair-use posture for user-uploaded books needs a clear
  policy before public launch.
- Retention beyond the novelty period is unproven; this applies to the
  post-MVP gamification loop (§7.1b) specifically, once it's built.
- Open-source governance model (license, contributor agreement, roadmap
  ownership) is not yet decided.
- Hackathon timeline: The Unicorn Track judging window is fixed by the AMD
  event schedule; scope must be trimmed aggressively to ship a demoable,
  containerized MVP by the submission deadline.
- Credit runway: Development is bounded by \$50 Fireworks AI credits (plus
  \$100 AMD Developer Cloud credits for new ADP members). Local Gemma
  inference and caching must be prioritized to keep the demo runnable
  throughout judging without hitting the credit cap.
