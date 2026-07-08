import os
import asyncio
from typing import List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.models.user import User, UserTier
from app.models.topic import Topic, Document, Node, Edge, ProcessingStatus
from app.auth.dependencies import get_current_user
from app.services.document_processor import process_documents, extract_text

router = APIRouter()

# Upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/atlas_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx"}

# File size limits by tier (in bytes)
FILE_SIZE_LIMITS = {
    UserTier.FREE: 5 * 1024 * 1024,      # 5 MB
    UserTier.TRIAL: 15 * 1024 * 1024,    # 15 MB
    UserTier.PREMIUM: 50 * 1024 * 1024,  # 50 MB
}


def validate_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return ext[1:]  # Remove the dot


def process_topic_documents_sync(topic_id: str):
    """Background task to process uploaded documents and generate mastery tree."""
    db = SessionLocal()
    try:
        # Get topic and documents
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return

        topic.status = ProcessingStatus.PROCESSING
        db.commit()

        # Get all documents for this topic
        documents = db.query(Document).filter(Document.topic_id == topic_id).all()

        # Prepare file info for processing
        file_paths = []
        for doc in documents:
            file_paths.append({
                'path': doc.file_path,
                'filename': doc.filename,
                'file_type': doc.file_type,
            })

            # Extract and store text if not already done
            if not doc.extracted_text:
                try:
                    doc.extracted_text = extract_text(doc.file_path, doc.file_type)
                except Exception as e:
                    print(f"Failed to extract text from {doc.filename}: {e}")

        db.commit()

        # Generate mastery tree (run async function in sync context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tree_data = loop.run_until_complete(process_documents(str(topic_id), file_paths))
        loop.close()

        # Update topic
        topic.title = tree_data.get("topic", "Untitled")
        topic.status = ProcessingStatus.COMPLETED
        topic.completed_at = datetime.utcnow()

        # Create nodes
        node_id_map = {}  # Map string IDs to UUID IDs
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
            db.flush()  # Get the UUID
            node_id_map[node_data["id"]] = node.id

        # Create edges
        for edge_data in tree_data.get("edges", []):
            source_id = node_id_map.get(edge_data["source"])
            target_id = node_id_map.get(edge_data["target"])
            if source_id and target_id:
                edge = Edge(
                    topic_id=topic_id,
                    source_node_id=source_id,
                    target_node_id=target_id,
                )
                db.add(edge)

        db.commit()
        print(f"Successfully processed topic {topic_id}: {topic.title}")

    except Exception as e:
        print(f"Failed to process topic {topic_id}: {e}")
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload documents for processing.
    Returns a topic_id that can be used to retrieve the generated tree.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Check file count limit
    max_files = 10 if current_user.tier == UserTier.PREMIUM else 5
    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_files} files allowed for your tier"
        )

    # Get file size limit for user's tier
    size_limit = FILE_SIZE_LIMITS.get(current_user.tier, FILE_SIZE_LIMITS[UserTier.FREE])

    # Create topic record
    topic = Topic(
        user_id=current_user.id,
        status=ProcessingStatus.PENDING,
    )
    db.add(topic)
    db.flush()  # Get the topic ID

    topic_id = topic.id
    topic_dir = os.path.join(UPLOAD_DIR, str(topic_id))
    os.makedirs(topic_dir, exist_ok=True)

    saved_files = []

    try:
        for file in files:
            # Validate file type
            if not validate_file(file.filename or ""):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Allowed: PDF, PPTX, DOCX"
                )

            # Read file content
            content = await file.read()

            # Check file size
            if len(content) > size_limit:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} exceeds size limit ({size_limit // (1024*1024)} MB)"
                )

            # Save file
            file_path = os.path.join(topic_dir, file.filename or f"file_{len(saved_files)}")
            with open(file_path, "wb") as f:
                f.write(content)

            # Create document record
            file_type = get_file_type(file.filename or "")
            document = Document(
                topic_id=topic_id,
                filename=file.filename or f"file_{len(saved_files)}",
                file_path=file_path,
                file_size=len(content),
                file_type=file_type,
            )
            db.add(document)

            saved_files.append({
                "filename": file.filename,
                "size": len(content),
            })

        # Update user's document count
        current_user.documents_used += len(saved_files)
        current_user.skill_trees_created += 1
        db.commit()

        # Start background processing
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
        # Clean up on error
        import shutil
        if os.path.exists(topic_dir):
            shutil.rmtree(topic_dir)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/ingest/{topic_id}/status")
async def get_processing_status(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the processing status of a topic."""
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return {
        "topic_id": str(topic.id),
        "title": topic.title,
        "status": topic.status.value,
        "error_message": topic.error_message,
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
