from fastapi import APIRouter

from app.services.graph import validate_graph

router = APIRouter()


@router.post("/validate")
def validate(payload: dict):
    """Pipeline step 5 — self-checking graph agent. See
    docs/concept-graph-pipeline.md step 5. Takes gpu-worker's POST
    /build-graph edges[] output and returns the repaired valid_dag plus a
    log of any edges dropped to break a cycle."""
    return validate_graph(payload["edges"])
