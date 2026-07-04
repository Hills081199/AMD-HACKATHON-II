# Atlas — turn any pile of documents into an optimal, playable learning path

Atlas extracts a concept-dependency graph from a messy folder of documents, computes the
optimal learning order with a topological sort, and renders it as a playable skill tree
with checkpoint quizzes.

## Repository layout (monorepo)

```
atlas/
├── apps/
│   ├── web/            # Next.js frontend — skill-tree UI (@xyflow/react)
│   └── api/             # FastAPI backend — orchestration, graph, endpoints
├── packages/
│   └── gpu-worker/      # AMD GPU / ROCm — embeddings, concept extraction, graph build
├── docker/               # One Dockerfile per service
├── docs/                 # Architecture notes, diagrams
├── data/                 # Sample data (e.g. mastery tree JSON) for local dev
├── docker-compose.yml
└── .env.example
```

## Quick start (local dev)

1. Copy environment variables:
   ```bash
   cp .env.example .env
   # fill in FIREWORKS_API_KEY, etc.
   ```

2. Run everything with Docker Compose:
   ```bash
   docker compose up --build
   ```
   - Frontend: http://localhost:3000
   - API: http://localhost:8000/health

3. Or run each service individually during development — see the README inside
   `apps/web`, `apps/api`, and `packages/gpu-worker`.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the pipeline diagram and the
reasoning behind the AMD GPU / Fireworks AI split.

## Submission checklist (hackathon)

- [ ] Public GitHub repo with README (this file)
- [ ] Containerized (`docker-compose.yml` + per-service Dockerfiles)
- [ ] Demo video + presentation slides
- [ ] Cover image, title, description, tags
- [ ] Live demo URL

## License

See [`LICENSE`](LICENSE).
