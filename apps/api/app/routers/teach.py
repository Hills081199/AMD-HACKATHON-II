from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.teach import FireworksClient, generate_lesson_package

router = APIRouter()

_fireworks = FireworksClient()


def get_fireworks_client() -> FireworksClient:
    return _fireworks


class ChunkIn(BaseModel):
    chunk_id: str
    doc_id: str
    page: int | None = None
    text: str


class LessonRequest(BaseModel):
    node_name: str
    chunks: list[ChunkIn]


@router.post("/{topic_id}/nodes/{node_id}/lesson")
def get_lesson(
    topic_id: str,
    node_id: str,
    request: LessonRequest,
    fireworks: FireworksClient = Depends(get_fireworks_client),
):
    """Pipeline step 7 — per-node lesson + quiz + real-world example
    (agentic RAG). See docs/concept-graph-pipeline.md's Teach stage. The
    caller supplies exactly this node's own source chunks[] (carried through
    from feat-001's chunk_id/doc_id since apps/api has no persisted
    chunk-text store yet — see notes in feature_list.json feat-007); this
    endpoint never has access to the rest of the corpus, so the retrieval
    scoping is enforced by the request shape itself."""
    return generate_lesson_package(request.node_name, [chunk.model_dump() for chunk in request.chunks], fireworks)
