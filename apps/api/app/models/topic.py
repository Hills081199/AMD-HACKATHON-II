"""
Database models for Topic, Document, Node, Edge, and UserProgress.
These store the generated mastery trees from uploaded documents.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

# Use String(36) for UUID - compatible with both SQLite and PostgreSQL

from app.db.database import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeStatus(str, enum.Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    COMPLETED = "completed"


class Topic(Base):
    """A topic represents a learning subject created from uploaded documents."""
    __tablename__ = "topics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)  # Generated from content
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    generation_duration_seconds = Column(Float, nullable=True)  # Time taken to generate the tree

    # Relationships
    user = relationship("User", back_populates="topics")
    documents = relationship("Document", back_populates="topic", cascade="all, delete-orphan")
    nodes = relationship("Node", back_populates="topic", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="topic", cascade="all, delete-orphan")


class Document(Base):
    """An uploaded document associated with a topic."""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, pptx, docx
    extracted_text = Column(Text, nullable=True)  # Extracted content
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    topic = relationship("Topic", back_populates="documents")


class Node(Base):
    """A node in the mastery tree (concept/skill)."""
    __tablename__ = "nodes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=False)
    title = Column(String(255), nullable=False)
    concept_key = Column(String(255), nullable=False)
    level = Column(Integer, default=0)  # Depth in the tree
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)

    # Lesson content
    lesson_summary = Column(Text, nullable=True)
    lesson_example = Column(Text, nullable=True)

    # Quiz data (JSON)
    quiz = Column(JSON, nullable=True)

    # Source references (JSON array)
    sources = Column(JSON, nullable=True)  # [{doc_id, title, page}, ...]

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    topic = relationship("Topic", back_populates="nodes")


class Edge(Base):
    """An edge connecting two nodes (prerequisite relationship)."""
    __tablename__ = "edges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=False)
    source_node_id = Column(String(36), ForeignKey("nodes.id"), nullable=False)
    target_node_id = Column(String(36), ForeignKey("nodes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    topic = relationship("Topic", back_populates="edges")
    source_node = relationship("Node", foreign_keys=[source_node_id])
    target_node = relationship("Node", foreign_keys=[target_node_id])


class UserProgress(Base):
    """Track user's progress on nodes."""
    __tablename__ = "user_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    node_id = Column(String(36), ForeignKey("nodes.id"), nullable=False)
    status = Column(SQLEnum(NodeStatus), default=NodeStatus.LOCKED)
    quiz_score = Column(Float, nullable=True)
    attempts = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    node = relationship("Node")
