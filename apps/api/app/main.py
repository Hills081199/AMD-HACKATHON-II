from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import graph, trees

app = FastAPI(title="Atlas API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before shipping past the hackathon
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trees.router, prefix="/trees", tags=["trees"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])


@app.get("/health")
def health():
    return {"status": "ok"}
