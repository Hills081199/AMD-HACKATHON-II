import json
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.topic import Topic, Node, Edge, ProcessingStatus
from app.services.quiz import grade_quiz
from app.services.teach import FireworksClient, generate_lesson_package

router = APIRouter()

_fireworks = FireworksClient()

# Gamification constants (mirrored from build_demo_dataset.py)
_DIFFICULTY_BADGE = {
    "foundational": "⭐ Foundational",
    "intermediate": "⭐⭐ Intermediate",
    "advanced": "⭐⭐⭐ Advanced",
}
_LEVEL_XP = {0: 50, 1: 100, 2: 150}
_LEVEL_MINUTES = {0: 10, 1: 15, 2: 20}

def _xp_reward(level: int) -> int:
    return _LEVEL_XP.get(level, 150 + (level - 2) * 25)

def _estimated_minutes(level: int) -> int:
    return _LEVEL_MINUTES.get(level, 20 + (level - 2) * 5)


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False

# Fallback to sample data for demo topic
if "SAMPLE_TREE_PATH" in os.environ:
    _SAMPLE_TREE_PATH = Path(os.environ["SAMPLE_TREE_PATH"])
else:
    try:
        _REPO_ROOT = Path(__file__).resolve().parents[4]
        _SAMPLE_TREE_PATH = _REPO_ROOT / "data" / "atlas_mastery_tree_sample.json"
    except IndexError:
        _SAMPLE_TREE_PATH = Path("/data/atlas_mastery_tree_sample.json")


def _load_sample_tree() -> dict:
    """Load the sample/demo tree from JSON file."""
    if not _SAMPLE_TREE_PATH.exists():
        raise HTTPException(status_code=404, detail="Demo tree data not available")
    return json.loads(_SAMPLE_TREE_PATH.read_text(encoding="utf-8"))


def _save_sample_tree(data: dict) -> None:
    """Persist updated tree data back to the JSON file (caching generated content)."""
    try:
        _SAMPLE_TREE_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        # Non-fatal — log and continue, frontend will still get the response
        print(f"[Trees] Warning: could not save updated tree to {_SAMPLE_TREE_PATH}: {exc}")


def _load_tree_from_db(topic_id: str, db: Session) -> Optional[dict]:
    """Load tree data from database."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        return None

    # Check if processing is complete
    if topic.status == ProcessingStatus.PENDING:
        return {
            "status": "pending",
            "message": "Processing has not started yet",
            "topic_id": str(topic.id),
        }
    elif topic.status == ProcessingStatus.PROCESSING:
        return {
            "status": "processing",
            "message": "Documents are being processed",
            "topic_id": str(topic.id),
        }
    elif topic.status == ProcessingStatus.FAILED:
        return {
            "status": "failed",
            "message": topic.error_message or "Processing failed",
            "topic_id": str(topic.id),
        }

    # Load nodes
    nodes = db.query(Node).filter(Node.topic_id == topic_id).all()
    edges = db.query(Edge).filter(Edge.topic_id == topic_id).all()

    # Build node ID mapping (UUID -> string ID for frontend)
    node_id_map = {}
    node_list = []

    for i, node in enumerate(nodes):
        node_str_id = f"n{i+1}"
        node_id_map[str(node.id)] = node_str_id

        # Determine prerequisites from edges
        prerequisites = []
        for edge in edges:
            if str(edge.target_node_id) == str(node.id):
                source_str_id = node_id_map.get(str(edge.source_node_id))
                if source_str_id:
                    prerequisites.append(source_str_id)

        # Determine status based on level (level 0 = unlocked, others = locked initially)
        status = "unlocked" if node.level == 0 else "locked"
        
        # Derive gamification fields
        # Note: In a real system, difficulty might be stored in the DB, 
        # but here we derive it based on level if not explicitly available.
        # Fallback heuristic: level 0 = foundational, else intermediate
        difficulty = "foundational" if node.level == 0 else "intermediate"

        node_data = {
            "id": node_str_id,
            "title": node.title,
            "concept_key": node.concept_key,
            "level": node.level,
            "difficulty": difficulty,
            "difficulty_badge": _DIFFICULTY_BADGE.get(difficulty, "⭐ Unknown"),
            "xp_reward": _xp_reward(node.level),
            "estimated_minutes": _estimated_minutes(node.level),
            "status": status,
            "prerequisites": prerequisites,
            "position": {
                "x": node.position_x,
                "y": node.position_y,
            },
            "lesson": {
                "summary": node.lesson_summary or "",
                "real_world_example": node.lesson_example or "",
            },
            "quiz": node.quiz,
            "sources": node.sources or [],
        }
        node_list.append(node_data)

    # Build edges list with string IDs (using from/to to match frontend)
    edge_list = []
    for edge in edges:
        source_str = node_id_map.get(str(edge.source_node_id))
        target_str = node_id_map.get(str(edge.target_node_id))
        if source_str and target_str:
            edge_list.append({
                "from": source_str,
                "to": target_str,
            })

    # Update prerequisites now that all node IDs are mapped
    for node_data in node_list:
        new_prereqs = []
        for edge in edges:
            target_str = node_id_map.get(str(edge.target_node_id))
            if target_str == node_data["id"]:
                source_str = node_id_map.get(str(edge.source_node_id))
                if source_str:
                    new_prereqs.append(source_str)
        node_data["prerequisites"] = new_prereqs

    return {
        "status": "completed",
        "topic": topic.title or "Untitled",
        "generated_at": topic.completed_at.isoformat() + "Z" if topic.completed_at else None,
        "nodes": node_list,
        "edges": edge_list,
    }


@router.get("/{topic_id}")
def get_tree(topic_id: str, db: Session = Depends(get_db)):
    """Return the mastery tree (nodes, edges, user_progress) for a topic."""
    # Handle demo topic or non-UUID topic_ids specially
    if topic_id == "demo" or not is_valid_uuid(topic_id):
        return _load_sample_tree()

    # Try to load from database
    tree_data = _load_tree_from_db(topic_id, db)

    if tree_data is None:
        # Fall back to sample data if topic not found
        # This helps during development/demo
        try:
            return _load_sample_tree()
        except:
            raise HTTPException(status_code=404, detail=f"No tree data available for topic_id={topic_id!r}")

    return tree_data


class QuizSubmission(BaseModel):
    answers: dict[str, int]


@router.post("/{topic_id}/nodes/{node_id}/submit-quiz")
def submit_quiz(
    topic_id: str,
    node_id: str,
    submission: QuizSubmission,
    db: Session = Depends(get_db),
):
    """Grade a node's checkpoint quiz."""
    # Handle demo topic or non-UUID topic_ids
    if topic_id == "demo" or not is_valid_uuid(topic_id):
        tree = _load_sample_tree()
        node = next((n for n in tree["nodes"] if n["id"] == node_id), None)
        if node is None:
            raise HTTPException(status_code=404, detail=f"No node {node_id!r} for topic_id={topic_id!r}")
        quiz = node.get("quiz")
        if not quiz:
            return {"node_id": node_id, "passed": True, "score": 100, "correct": 0, "total": 0}
        result = grade_quiz(quiz, submission.answers)
        return {"node_id": node_id, **result}

    # Load from database
    tree_data = _load_tree_from_db(topic_id, db)
    if not tree_data or tree_data.get("status") != "completed":
        raise HTTPException(status_code=404, detail=f"Tree not available for topic_id={topic_id!r}")

    node = next((n for n in tree_data.get("nodes", []) if n["id"] == node_id), None)
    if node is None:
        raise HTTPException(status_code=404, detail=f"No node {node_id!r} for topic_id={topic_id!r}")

    quiz = node.get("quiz")
    if not quiz:
        return {"node_id": node_id, "passed": True, "score": 100, "correct": 0, "total": 0}

    result = grade_quiz(quiz, submission.answers)
    return {"node_id": node_id, **result}


@router.post("/{topic_id}/nodes/{node_id}/generate-lesson")
def generate_lesson(
    topic_id: str,
    node_id: str,
    db: Session = Depends(get_db),
):
    """On-demand lesson + quiz generation for a single node (Step 7).

    Smart cache: if the node already has a non-empty lesson.summary AND quiz
    questions, returns the cached content immediately without calling the LLM.
    Otherwise, calls Fireworks AI to generate lesson + quiz, persists the
    result back to disk (for JSON-backed topics) or DB (for real topics),
    and returns the generated content.
    """
    # ── Demo / non-UUID path (JSON-backed) ────────────────────────────────
    if topic_id == "demo" or not is_valid_uuid(topic_id):
        tree = _load_sample_tree()
        node = next((n for n in tree["nodes"] if n["id"] == node_id), None)
        if node is None:
            raise HTTPException(status_code=404, detail=f"No node {node_id!r} for topic_id={topic_id!r}")

        # Cache check
        lesson = node.get("lesson") or {}
        quiz = node.get("quiz") or {}
        questions = quiz.get("questions", [])
        if lesson.get("summary", "").strip() and questions:
            # Already generated — serve from cache
            return {
                "node_id": node_id,
                "cached": True,
                "lesson": lesson.get("summary", ""),
                "example": lesson.get("real_world_example", ""),
                "quiz": quiz,
            }

        # Build chunk list from sources (we don't have raw text, so create
        # a synthetic chunk from the node title + doc_id for the prompt)
        sources = node.get("sources") or []
        chunks = []
        for src in sources:
            chunks.append({
                "chunk_id": f"{src.get('doc_id', 'doc')}:p{src.get('page', 0)}",
                "doc_id": src.get("doc_id", "unknown"),
                "page": src.get("page"),
                "text": (
                    f"[Source: {src.get('doc_id', 'unknown')}, page {src.get('page', '?')}] "
                    f"Concept: {node.get('title', node_id)}. "
                    f"This concept is at level {node.get('level', 0)} in the learning tree."
                ),
            })

        # Fallback if no sources: use node title as minimal context
        if not chunks:
            chunks = [{
                "chunk_id": f"synthetic_{node_id}",
                "doc_id": "synthetic",
                "page": None,
                "text": (
                    f"Concept: {node.get('title', node_id)}. "
                    f"Level: {node.get('level', 0)}. "
                    f"Difficulty: {node.get('difficulty', 'foundational')}."
                ),
            }]

        # Prerequisite names for context (IMP-B3)
        prereq_ids = node.get("prerequisites") or []
        prereq_names = []
        for pid in prereq_ids:
            prereq_node = next((n for n in tree["nodes"] if n["id"] == pid), None)
            if prereq_node:
                prereq_names.append(prereq_node.get("title", pid))

        # Generate via Fireworks
        try:
            package = generate_lesson_package(
                node_name=node.get("title", node_id),
                chunks=chunks,
                fireworks=_fireworks,
                prerequisite_names=prereq_names,
                node_level=node.get("level", 0),
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}")

        # Build quiz structure matching the JSON schema
        all_questions = package.get("questions", [])
        if not all_questions and package.get("quiz", {}).get("question"):
            legacy_q = package["quiz"]
            all_questions = [{"difficulty": "medium", **legacy_q}]

        questions_with_ids = [
            {
                "id": f"q_{node_id}_{idx + 1}",
                "type": "mcq",
                "difficulty": q.get("difficulty", "medium"),
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "answer_index": q.get("answer_index", 0),
            }
            for idx, q in enumerate(all_questions)
            if q.get("question")
        ]

        quiz_obj = {
            "id": f"q_{node_id}",
            "pass_threshold": package.get("pass_threshold", 0.6),
            "questions": questions_with_ids,
        }

        lesson_obj = {
            "summary": package.get("lesson", ""),
            "real_world_example": package.get("example", ""),
        }

        # Persist back to JSON file (cache)
        node["lesson"] = lesson_obj
        node["quiz"] = quiz_obj
        _save_sample_tree(tree)

        return {
            "node_id": node_id,
            "cached": False,
            "lesson": lesson_obj["summary"],
            "example": lesson_obj["real_world_example"],
            "quiz": quiz_obj,
        }

    # ── Database-backed path ───────────────────────────────────────────────
    tree_data = _load_tree_from_db(topic_id, db)
    if not tree_data or tree_data.get("status") != "completed":
        raise HTTPException(status_code=404, detail=f"Tree not available for topic_id={topic_id!r}")

    node = next((n for n in tree_data.get("nodes", []) if n["id"] == node_id), None)
    if node is None:
        raise HTTPException(status_code=404, detail=f"No node {node_id!r} for topic_id={topic_id!r}")

    # Cache check
    lesson = node.get("lesson") or {}
    quiz = node.get("quiz") or {}
    questions = quiz.get("questions", [])
    if lesson.get("summary", "").strip() and questions:
        return {
            "node_id": node_id,
            "cached": True,
            "lesson": lesson.get("summary", ""),
            "example": lesson.get("real_world_example", ""),
            "quiz": quiz,
        }

    # Build minimal chunk from node metadata
    sources = node.get("sources") or []
    chunks = []
    for src in sources:
        chunks.append({
            "chunk_id": f"{src.get('doc_id', 'doc')}:p{src.get('page', 0)}",
            "doc_id": src.get("doc_id", "unknown"),
            "page": src.get("page"),
            "text": (
                f"[Source: {src.get('doc_id', 'unknown')}, page {src.get('page', '?')}] "
                f"Concept: {node.get('title', node_id)}."
            ),
        })
    if not chunks:
        chunks = [{
            "chunk_id": f"synthetic_{node_id}",
            "doc_id": "synthetic",
            "page": None,
            "text": f"Concept: {node.get('title', node_id)}.",
        }]

    try:
        package = generate_lesson_package(
            node_name=node.get("title", node_id),
            chunks=chunks,
            fireworks=_fireworks,
            node_level=node.get("level", 0),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}")

    all_questions = package.get("questions", [])
    questions_with_ids = [
        {
            "id": f"q_{node_id}_{idx + 1}",
            "type": "mcq",
            "difficulty": q.get("difficulty", "medium"),
            "question": q.get("question", ""),
            "options": q.get("options", []),
            "answer_index": q.get("answer_index", 0),
        }
        for idx, q in enumerate(all_questions)
        if q.get("question")
    ]
    quiz_obj = {
        "id": f"q_{node_id}",
        "pass_threshold": package.get("pass_threshold", 0.6),
        "questions": questions_with_ids,
    }
    lesson_obj = {
        "summary": package.get("lesson", ""),
        "real_world_example": package.get("example", ""),
    }

    # Persist to DB — find the actual Node record by matching title/concept_key
    # node_id here is the string ID (e.g. "n1"), we need to look up the DB row
    db_nodes = db.query(Node).filter(Node.topic_id == topic_id).all()
    # Map string IDs back to DB nodes (same ordering as _load_tree_from_db)
    for i, db_node in enumerate(db_nodes):
        if f"n{i+1}" == node_id:
            db_node.lesson_summary = lesson_obj["summary"]
            db_node.lesson_example = lesson_obj["real_world_example"]
            db_node.quiz = quiz_obj
            db.commit()
            break

    return {
        "node_id": node_id,
        "cached": False,
        "lesson": lesson_obj["summary"],
        "example": lesson_obj["real_world_example"],
        "quiz": quiz_obj,
    }
