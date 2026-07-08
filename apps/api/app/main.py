from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import graph, teach, trees, auth, user, admin
from app.db.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Atlas API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before shipping past the hackathon
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Auth routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Existing routes
app.include_router(trees.router, prefix="/trees", tags=["trees"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
app.include_router(teach.router, prefix="/trees", tags=["teach"])


@app.get("/health")
def health():
    return {"status": "ok"}
