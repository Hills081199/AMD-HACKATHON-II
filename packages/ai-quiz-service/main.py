from fastapi import FastAPI

from api.routes import router as quiz_router

app = FastAPI(
    title="Atlas Quiz Generation Service",
    description="AI-powered quiz generation microservice for Atlas.",
    version="1.0.0",
)

app.include_router(quiz_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Atlas Quiz Generation Service",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
    }