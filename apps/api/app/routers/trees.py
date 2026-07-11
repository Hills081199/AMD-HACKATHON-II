import json
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.topic import Topic, Node, Edge, Document, ProcessingStatus
from app.services.quiz import grade_quiz
from app.services.teach import FireworksClient, generate_lesson_package

router = APIRouter()


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

        node_data = {
            "id": node_str_id,
            "title": node.title,
            "concept_key": node.concept_key,
            "level": node.level,
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


@router.post("/{topic_id}/nodes/{node_id}/regenerate-quiz")
def regenerate_quiz(
    topic_id: str,
    node_id: str,
    db: Session = Depends(get_db),
):
    """Regenerate quiz for an existing node using its source documents."""
    if not is_valid_uuid(topic_id):
        raise HTTPException(status_code=400, detail="Invalid topic_id")

    # Get the topic
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")

    # Get all nodes to find the one matching node_id (which is like "n1", "n2", etc.)
    nodes = db.query(Node).filter(Node.topic_id == topic_id).all()

    # Build node ID mapping
    node_id_map = {}
    db_node = None
    for i, node in enumerate(nodes):
        node_str_id = f"n{i+1}"
        node_id_map[node_str_id] = node
        if node_str_id == node_id:
            db_node = node

    if not db_node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    # Get documents for this topic to build chunks
    documents = db.query(Document).filter(Document.topic_id == topic_id).all()

    # Build chunks from document extracted text or read from PDF
    node_chunks = []
    for doc in documents:
        text = None
        if doc.extracted_text:
            text = doc.extracted_text[:4000]
        elif doc.file_path and Path(doc.file_path).exists():
            # Try to extract text from PDF
            try:
                import fitz  # PyMuPDF
                pdf_doc = fitz.open(doc.file_path)
                text_parts = []
                for page in pdf_doc:
                    text_parts.append(page.get_text())
                text = "\n".join(text_parts)[:4000]
                pdf_doc.close()
            except Exception:
                pass

        if text:
            node_chunks.append({
                "chunk_id": f"{doc.id}_chunk_0",
                "doc_id": doc.id,
                "page": 1,
                "text": text,
            })

    # Fallback: use node title and concept as context if no document text
    if not node_chunks:
        # Create a minimal context from the node itself
        context_text = f"""
Topic: {topic.title or 'Learning Topic'}
Concept: {db_node.title}
This is a learning module about {db_node.title}. Generate educational quiz questions
to test understanding of this concept in the context of the broader topic.
"""
        node_chunks.append({
            "chunk_id": f"{db_node.id}_context",
            "doc_id": "generated",
            "page": 1,
            "text": context_text,
        })

    # Get prerequisites
    edges = db.query(Edge).filter(Edge.topic_id == topic_id).all()
    prereq_names = []
    for edge in edges:
        if str(edge.target_node_id) == str(db_node.id):
            prereq_node = next((n for n in nodes if str(n.id) == str(edge.source_node_id)), None)
            if prereq_node:
                prereq_names.append(prereq_node.title)

    # Generate lesson + quiz
    try:
        client = FireworksClient()
        package = generate_lesson_package(
            db_node.title,
            node_chunks,
            client,
            prerequisite_names=prereq_names,
            node_level=db_node.level,
            max_attempts=2,
        )

        # Update node with new lesson and quiz
        db_node.lesson_summary = package.get("lesson", "")
        db_node.lesson_example = package.get("example", "")

        questions = package.get("questions", [])
        if questions:
            db_node.quiz = {
                "questions": [
                    {
                        "id": f"{db_node.id}_q{i}",
                        "question": q.get("question", ""),
                        "options": q.get("options", []),
                        "answer_index": q.get("answer_index", 0),
                        "difficulty": q.get("difficulty", "medium"),
                    }
                    for i, q in enumerate(questions)
                ],
                "pass_threshold": package.get("pass_threshold", 0.6),
            }

        db.commit()

        return {
            "success": True,
            "node_id": node_id,
            "lesson": {
                "summary": db_node.lesson_summary,
                "real_world_example": db_node.lesson_example,
            },
            "quiz": db_node.quiz,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")
