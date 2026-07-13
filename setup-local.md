# Atlas — Local Setup & Run Guide (No Docker)

**Note:** Our track does not allow Docker. This guide runs every service directly on the host machine.

---

## Prerequisites

- **Node.js** 20.x (for the frontend)
- **Python 3.11** (⚠️ not 3.13/3.14 — `pydantic-core` has no prebuilt wheel for newer Python versions and will fail to install without a Rust/MSVC toolchain)
- **Git**

Check what's installed:
```powershell
node -v
py -0
```
If Python 3.11 is missing, download it here: https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
During install, tick **"Add python.exe to PATH"**.

---

## 1. Clone & environment variables

```powershell
git clone https://github.com/Hills081199/AMD-HACKATHON-II.git
cd AMD-HACKATHON-II
copy .env.example .env
```
Open `.env` and fill in required values (e.g. `FIREWORKS_API_KEY`).

---

## 2. Backend (FastAPI) — `apps/api`

```powershell
cd apps/api
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify it's running:
```
http://localhost:8000/health
```

Keep this terminal open — the backend needs to stay running.

---

## 3. Frontend (Next.js) — `apps/web`

Open a **new terminal** (keep the backend terminal running):

```powershell
cd apps/web
npm install
npm run dev
```

Open in browser:
```
http://localhost:3000
```

The frontend reads the API URL from `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000` if unset in `.env`).

---

## 4. GPU Worker (ROCm) — `packages/gpu-worker`

This requires an actual AMD GPU with ROCm installed — it will **not** run on a laptop without one. Use it only on:
- The AMD Developer Cloud GPU instance, or
- A machine with ROCm properly installed and an AMD GPU present.

```bash
cd packages/gpu-worker
python3.11 -m venv venv
source venv/bin/activate      # Linux/Mac; on the AMD Cloud instance this will be Linux
pip install -r requirements.txt
python worker.py              # or the actual entrypoint — check packages/gpu-worker/README.md
```

Verify GPU is visible before running:
```bash
rocm-smi
```

For local development on a non-GPU laptop, skip this step — the frontend and backend can still be tested end-to-end using the sample data in `/data` (e.g. `demo_tree_generated.json`, `3b.loss-functions.json`) without the GPU worker running.

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| `pydantic-core` fails to build / `link.exe not found` | You're on Python 3.13+. Reinstall with Python 3.11 (see Prerequisites). |
| `Failed to fetch` on the Upload page | Normal if the GPU worker isn't running locally — that pipeline needs ROCm. Test on the AMD Developer Cloud instance. |
| `Failed to fetch` on the `/tree` page | The backend (`apps/api`) isn't running — start it first (Step 2), then reload. |
| `npm run build` fails with a TypeScript error | Someone pushed a type error — check the exact file/line in the error output and fix the type mismatch (don't ignore it, it will fail on any judge's machine too). |
| Port already in use (3000 or 8000) | Another process is using that port — close it, or run `npx kill-port 3000` / `npx kill-port 8000`. |

---

## Running Everything Together (quick reference)

| Terminal | Command | URL |
|---|---|---|
| 1 — Backend | `cd apps/api && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000` | http://localhost:8000/health |
| 2 — Frontend | `cd apps/web && npm run dev` | http://localhost:3000 |
| 3 — GPU Worker (AMD Cloud only) | `cd packages/gpu-worker && python worker.py` | — |

Both Terminal 1 and 2 must stay open and running at the same time for the app to work end-to-end (without the upload/GPU pipeline).