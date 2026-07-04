# Base image: swap for the ROCm-provided base image from the hackathon
# organizers if one is given (it will already have ROCm drivers configured).
FROM rocm/pytorch:latest

WORKDIR /app
COPY packages/gpu-worker/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/gpu-worker/ ./

EXPOSE 8100
CMD ["uvicorn", "worker.main:app", "--host", "0.0.0.0", "--port", "8100"]
