import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

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


@router.get("/{topic_id}")
def get_tree(topic_id: str):
    """Return the mastery tree (nodes, edges, user_progress) for a topic."""
    if not _SAMPLE_TREE_PATH.exists():
        raise HTTPException(status_code=404, detail=f"No tree data available for topic_id={topic_id!r}")
    return json.loads(_SAMPLE_TREE_PATH.read_text(encoding="utf-8"))


@router.post("/{topic_id}/nodes/{node_id}/submit-quiz")
def submit_quiz(topic_id: str, node_id: str, answers: dict):
    """Grade the quiz for a node; if passed, mark completed and unlock children."""
    raise HTTPException(status_code=501, detail="TODO: grade quiz, update status, unlock children")
