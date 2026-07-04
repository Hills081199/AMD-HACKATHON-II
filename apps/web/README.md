# Atlas — web (Next.js)

## Dev
```bash
npm install
npm run dev
```
Runs on http://localhost:3000. Set `NEXT_PUBLIC_API_URL` in the root `.env`
to point at the API (defaults to http://localhost:8000).

Skill-tree page: `app/tree/page.tsx` — wire it up to
`@xyflow/react`, reading `/data/atlas_mastery_tree_sample.json` for local
dev, or `GET {NEXT_PUBLIC_API_URL}/trees/{topic_id}` once the API is ready.
