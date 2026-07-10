<div align="center">

# Atlas

**Turn any pile of documents into an optimal, playable learning path.**

Atlas extracts a concept-dependency graph from a messy folder of documents, computes the optimal learning order with a topological sort, and renders it as a playable skill tree with checkpoint quizzes.

[![Hackathon](https://img.shields.io/badge/AMD%20Developer%20Hackathon-Track%203%20Unicorn-000000?style=flat-square)](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-000000?style=flat-square&logo=nextdotjs&logoColor=white)](apps/web)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](apps/api)
[![GPU](https://img.shields.io/badge/GPU-AMD%20ROCm-ED1C24?style=flat-square&logo=amd&logoColor=white)](packages/gpu-worker)
[![Reasoning](https://img.shields.io/badge/Reasoning-Fireworks%20AI-6C47FF?style=flat-square)](https://fireworks.ai)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## Table of Contents

- [Repository Layout](#repository-layout-monorepo)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Submission Checklist](#submission-checklist-hackathon)
- [License](#license)

---

## Repository Layout (monorepo)

```
atlas/
├── apps/
│   ├── web/              # Next.js frontend — skill-tree UI (@xyflow/react)
│   └── api/               # FastAPI backend — orchestration, graph, endpoints
├── packages/
│   └── gpu-worker/        # AMD GPU / ROCm — embeddings, concept extraction, graph build
├── docker/                 # One Dockerfile per service
├── docs/                   # Architecture notes, diagrams
├── data/                   # Sample data (e.g. mastery tree JSON) for local dev
├── docker-compose.yml
└── .env.example
```

## Quick Start

### 1. Environment variables

```bash
cp .env.example .env
# fill in FIREWORKS_API_KEY, etc.
```

### 2. Run the services

This track does not permit Docker for submission, so every service is run directly on the host.

**Backend (FastAPI) — `apps/api`**

```bash
cd apps/api
python3.11 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify: `http://localhost:8000/health`

> Use Python 3.11. Newer versions (3.13+) do not have a prebuilt `pydantic-core` wheel and will fail to install without a Rust/MSVC toolchain.

**Frontend (Next.js) — `apps/web`** — in a separate terminal, backend must stay running

```bash
cd apps/web
npm install
npm run dev
```

Open: `http://localhost:3000`

**GPU Worker (ROCm) — `packages/gpu-worker`** — requires an actual AMD GPU with ROCm (AMD Developer Cloud instance, not a local laptop without one)

```bash
cd packages/gpu-worker
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python worker.py
```

Verify GPU visibility: `rocm-smi`

Frontend and backend can be developed and tested end-to-end using the sample data in `/data` without the GPU worker running.

### 3. Per-service documentation

See the README inside `apps/web`, `apps/api`, and `packages/gpu-worker` for service-specific details.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the pipeline diagram and the reasoning behind the AMD GPU / Fireworks AI split.

## Submission Checklist (hackathon)

- [ ] Public GitHub repo with README (this file)
- [ ] Fully runnable without Docker (per track rules)
- [ ] Demo video + presentation slides
- [ ] Cover image, title, description, tags
- [ ] Live demo URL

## License

See [`LICENSE`](LICENSE).
