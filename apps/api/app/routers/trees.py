import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.quiz import grade_quiz

router = APIRouter()

# TODO: replace with real storage (DB or the live pipeline's generated graph
# output — feat-002's concepts + feat-004's valid_dag through feat-005's
# assign_levels()). For now, serves the static sample dataset regardless of
# topic_id, per docs/architecture.md's note that this file is "the exact
# shape the frontend should expect." Not copied into the Docker image yet
# (see docker/api.Dockerfile) — override via SAMPLE_TREE_PATH once that's
# wired up for a containerized deployment.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_SAMPLE_TREE_PATH = Path(
    os.environ.get("SAMPLE_TREE_PATH", str(_REPO_ROOT / "data" / "atlas_mastery_tree_sample.json"))
)


def _load_tree(topic_id: str) -> dict:
    if not _SAMPLE_TREE_PATH.exists():
        raise HTTPException(status_code=404, detail=f"No tree data available for topic_id={topic_id!r}")
    return json.loads(_SAMPLE_TREE_PATH.read_text(encoding="utf-8"))


@router.get("/{topic_id}")
def get_tree(topic_id: str):
    """Return the mastery tree (nodes, edges, user_progress) for a topic."""
    return _load_tree(topic_id)


class QuizSubmission(BaseModel):
    answers: dict[str, int]


@router.post("/{topic_id}/nodes/{node_id}/submit-quiz")
def submit_quiz(topic_id: str, node_id: str, submission: QuizSubmission):
    """Grade a node's checkpoint quiz. Does not persist status server-side
    (there's no storage layer yet — see feat-007's same-shaped scope note);
    the client (apps/web's progressStore, per feat-006) is the source of
    truth for which nodes are completed, and marks this node completed only
    when `passed` comes back true here, which in turn drives feat-006's
    existing unlock logic for its children."""
    tree = _load_tree(topic_id)
    node = next((candidate for candidate in tree["nodes"] if candidate["id"] == node_id), None)
    if node is None:
        raise HTTPException(status_code=404, detail=f"No node {node_id!r} for topic_id={topic_id!r}")
    quiz = node.get("quiz")
    if quiz is None:
        raise HTTPException(status_code=404, detail=f"Node {node_id!r} has no quiz")

    result = grade_quiz(quiz, submission.answers)
    return {"node_id": node_id, **result}
