# Atlas — API (FastAPI)

## Dev
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Health check: http://localhost:8000/health

Endpoints to implement: see `app/routers/trees.py`.
