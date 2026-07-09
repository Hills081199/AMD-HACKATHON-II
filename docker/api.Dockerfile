FROM python:3.11-slim

WORKDIR /app

# Install API dependencies
COPY apps/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install gpu-worker dependencies (needed for the pipeline)
COPY packages/gpu-worker/requirements.txt ./gpu_worker_requirements.txt
RUN pip install --no-cache-dir -r gpu_worker_requirements.txt || true

# Copy gpu-worker package so it can be imported
COPY packages/gpu-worker/ /gpu-worker/

# Copy API source
COPY apps/api/ ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
