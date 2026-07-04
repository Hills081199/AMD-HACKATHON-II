# Atlas — GPU worker (AMD ROCm)

## Dev
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
pip install -r requirements.txt
uvicorn worker.main:app --reload --port 8100
```

Verify ROCm/torch is picking up the GPU **on day 1** — this is the most
common early blocker in AMD-GPU hackathons.
