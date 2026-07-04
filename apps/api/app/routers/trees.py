from fastapi import APIRouter, HTTPException

router = APIRouter()

# TODO: replace with real storage (DB or generated graph output from the
# gpu-worker). For now, load the sample JSON in /data for local dev.


@router.get("/{topic_id}")
def get_tree(topic_id: str):
    """Return the mastery tree (nodes, edges, user_progress) for a topic."""
    raise HTTPException(status_code=501, detail="TODO: load generated graph for topic_id")


@router.post("/{topic_id}/nodes/{node_id}/submit-quiz")
def submit_quiz(topic_id: str, node_id: str, answers: dict):
    """Grade the quiz for a node; if passed, mark completed and unlock children."""
    raise HTTPException(status_code=501, detail="TODO: grade quiz, update status, unlock children")
