import os
import asyncio
import tempfile
from typing import List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.models.user import User, UserTier
from app.models.topic import Topic, Document, Node, Edge, ProcessingStatus
from app.auth.dependencies import get_current_user, get_current_user_mock
from app.services.document_processor import process_documents, extract_text

router = APIRouter()

# Upload directory — works on both Windows and Linux
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "atlas_uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx"}

# File size limits by tier (in bytes)
FILE_SIZE_LIMITS = {
    UserTier.FREE: 5 * 1024 * 1024,      # 5 MB
    UserTier.TRIAL: 15 * 1024 * 1024,    # 15 MB
    UserTier.PREMIUM: 50 * 1024 * 1024,  # 50 MB
}

# Human-readable labels for each pipeline step sent to the frontend
STEP_LABELS = {
    "chunking":   "📄 Chunking documents…",
    "extracting": "🧠 Extracting concepts…",
    "clustering": "🔗 Clustering & deduplicating…",
    "inferring":  "🔍 Inferring prerequisites…",
    "validating": "✅ Validating dependency graph…",
    "leveling":   "🏗️ Assigning concept tiers…",
    "building":   "🛠️ Assembling learning tree…",
    "done":       "🎉 Pipeline complete!",
}


def validate_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return ext[1:]  # Remove the dot


def process_topic_documents_sync(topic_id: str):
    """Background task: run the full Steps 1-6 pipeline over uploaded docs."""
    db = SessionLocal()
    try:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return

        topic.status = ProcessingStatus.PROCESSING
        topic.error_message = STEP_LABELS["chunking"]
        db.commit()

        documents = db.query(Document).filter(Document.topic_id == topic_id).all()

        file_paths = []
        for doc in documents:
            file_paths.append({
                "path": doc.file_path,
                "filename": doc.filename,
                "file_type": doc.file_type,
            })

        def _progress(step: str, detail: str) -> None:
            """Update topic.error_message with current step label (visible via status endpoint)."""
            label = STEP_LABELS.get(step, step)
            try:
                db_inner = SessionLocal()
                t = db_inner.query(Topic).filter(Topic.id == topic_id).first()
                if t and t.status == ProcessingStatus.PROCESSING:
                    t.error_message = label
                    db_inner.commit()
                db_inner.close()
            except Exception:
                pass  # best-effort; don't crash the pipeline

        # Run the async pipeline in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tree_data = loop.run_until_complete(
            process_documents(str(topic_id), file_paths, progress_callback=_progress)
        )
        loop.close()

        # Save the raw pipeline JSON result to disk using the first document's name
        if file_paths:
            import json
            first_filename = file_paths[0]["filename"]
            base_name = os.path.splitext(first_filename)[0]
            # Use /data inside docker, or ./data locally
            data_dir = "/data/generated" if os.path.exists("/data") else os.path.join(os.getcwd(), "data", "generated")
            os.makedirs(data_dir, exist_ok=True)
            out_path = os.path.join(data_dir, f"{base_name}.json")
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(tree_data, f, ensure_ascii=False, indent=2)
                print(f"[Ingest] Saved generated JSON tree to {out_path}")
            except Exception as e:
                print(f"[Ingest] Warning: Failed to save JSON file {out_path}: {e}")

        # Persist results: topic title
        topic.title = tree_data.get("topic", f"Topic {str(topic_id)[:8]}")
        topic.status = ProcessingStatus.COMPLETED
        topic.error_message = None
        topic.completed_at = datetime.utcnow()

        # Persist nodes
        node_id_map: dict[str, object] = {}  # pipeline str ID → DB UUID
        for node_data in tree_data.get("nodes", []):
            node = Node(
                topic_id=topic_id,
                title=node_data["title"],
                concept_key=node_data.get("concept_key", node_data["title"].lower().replace(" ", "_")),
                level=node_data.get("level", 0),
                position_x=node_data.get("position", {}).get("x", 0),
                position_y=node_data.get("position", {}).get("y", 0),
                lesson_summary=node_data.get("lesson", {}).get("summary"),
                lesson_example=node_data.get("lesson", {}).get("real_world_example"),
                quiz=node_data.get("quiz"),
                sources=node_data.get("sources"),
            )
            db.add(node)
            db.flush()
            node_id_map[node_data["id"]] = node.id

        # Persist edges (pipeline uses "from"/"to")
        for edge_data in tree_data.get("edges", []):
            source_id = node_id_map.get(edge_data.get("from") or edge_data.get("source"))
            target_id = node_id_map.get(edge_data.get("to") or edge_data.get("target"))
            if source_id and target_id:
                edge = Edge(
                    topic_id=topic_id,
                    source_node_id=source_id,
                    target_node_id=target_id,
                )
                db.add(edge)

        db.commit()
        print(f"[Ingest] Successfully processed topic {topic_id}: {topic.title}")

    except Exception as e:
        print(f"[Ingest] Failed to process topic {topic_id}: {e}")
        import traceback
        traceback.print_exc()
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if topic:
            topic.status = ProcessingStatus.FAILED
            topic.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/ingest")
async def ingest_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Upload documents for processing.
    Returns a topic_id that can be used to track processing status and
    retrieve the generated tree.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    max_files = 10 if current_user.tier == UserTier.PREMIUM else 5
    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_files} files allowed for your tier",
        )

    size_limit = FILE_SIZE_LIMITS.get(current_user.tier, FILE_SIZE_LIMITS[UserTier.FREE])

    # Create topic record
    topic = Topic(
        user_id=current_user.id,
        status=ProcessingStatus.PENDING,
    )
    db.add(topic)
    db.flush()

    topic_id = topic.id
    topic_dir = os.path.join(UPLOAD_DIR, str(topic_id))
    os.makedirs(topic_dir, exist_ok=True)

    saved_files = []

    try:
        for file in files:
            if not validate_file(file.filename or ""):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Allowed: PDF, PPTX, DOCX",
                )

            content = await file.read()

            if len(content) > size_limit:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} exceeds size limit ({size_limit // (1024*1024)} MB)",
                )

            file_path = os.path.join(topic_dir, file.filename or f"file_{len(saved_files)}")
            with open(file_path, "wb") as f:
                f.write(content)

            file_type = get_file_type(file.filename or "")
            document = Document(
                topic_id=topic_id,
                filename=file.filename or f"file_{len(saved_files)}",
                file_path=file_path,
                file_size=len(content),
                file_type=file_type,
            )
            db.add(document)

            saved_files.append({"filename": file.filename, "size": len(content)})

        current_user.documents_used += len(saved_files)
        current_user.skill_trees_created += 1
        db.commit()

        background_tasks.add_task(process_topic_documents_sync, str(topic_id))

        return {
            "success": True,
            "topic_id": str(topic_id),
            "files_uploaded": len(saved_files),
            "files": saved_files,
            "message": "Files uploaded successfully. Processing will begin shortly.",
            "status": "processing",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import shutil
        if os.path.exists(topic_dir):
            shutil.rmtree(topic_dir)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/ingest/{topic_id}/status")
async def get_processing_status(
    topic_id: str,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get the processing status of a topic.

    During processing, `current_step` reflects which pipeline step is running.
    On failure, `error_message` contains the error description.
    """
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id,
    ).first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # While processing, error_message holds the current step label
    current_step = None
    error_message = None
    if topic.status == ProcessingStatus.PROCESSING:
        current_step = topic.error_message  # repurposed as step tracker
    elif topic.status == ProcessingStatus.FAILED:
        error_message = topic.error_message

    return {
        "topic_id": str(topic.id),
        "title": topic.title,
        "status": topic.status.value,
        "current_step": current_step,
        "error_message": error_message,
        "created_at": topic.created_at.isoformat() if topic.created_at else None,
        "completed_at": topic.completed_at.isoformat() if topic.completed_at else None,
    }


@router.post("/ingest/demo")
async def ingest_demo():
    """
    Return the demo topic_id without authentication.
    For hackathon demo purposes.
    """
    return {
        "success": True,
        "topic_id": "demo",
        "message": "Using demo dataset",
    }
