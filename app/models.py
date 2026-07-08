from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    owner_id = Column(String, index=True)
    created_at = Column(DateTime, default=get_utc_now)

    # Relationships
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="project", cascade="all, delete-orphan")
    guided_state = relationship("GuidedState", back_populates="project", uselist=False, cascade="all, delete-orphan")
    essay_memory = relationship("EssayMemory", back_populates="project", uselist=False, cascade="all, delete-orphan")
    essay_chunks = relationship("EssayChunk", back_populates="project", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    content = Column(Text, default="")
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    # Relationship
    project = relationship("Project", back_populates="documents")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    mode = Column(String)  # ensayo, critica, estilo, mejora
    user_input = Column(Text)
    ai_output = Column(Text)
    model_used = Column(String, default="")
    fallback_used = Column(Integer, default=0)
    prompt_tokens_estimate = Column(Integer, default=0)
    completion_tokens_estimate = Column(Integer, default=0)
    total_tokens_estimate = Column(Integer, default=0)
    context_chars = Column(Integer, default=0)
    timestamp = Column(DateTime, default=get_utc_now)

    # Relationship
    project = relationship("Project", back_populates="interactions")

class GuidedState(Base):
    __tablename__ = "guided_states"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True)
    current_stage = Column(String, default="idea") 
    accumulated_content = Column(Text, default="")
    stage_idea = Column(Text, default="")
    stage_estructura = Column(Text, default="")
    stage_introduccion = Column(Text, default="")
    stage_desarrollo = Column(Text, default="")
    stage_contraargumento = Column(Text, default="")
    stage_conclusion = Column(Text, default="")
    
    # Relationship
    project = relationship("Project", back_populates="guided_state")


class EssayMemory(Base):
    __tablename__ = "essay_memories"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True, index=True)
    thesis = Column(Text, default="")
    memory_notes = Column(Text, default="")
    chunk_count = Column(Integer, default=0)
    document_hash = Column(String(64), default="")
    map_summary = Column(Text, default="")
    global_summary = Column(Text, default="")
    summary_status = Column(String, default="idle")
    summary_error = Column(Text, default="")
    summary_hash = Column(String(64), default="")
    rag_status = Column(String, default="idle")
    rag_error = Column(Text, default="")
    rag_hash = Column(String(64), default="")
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    # Relationship
    project = relationship("Project", back_populates="essay_memory")


class EssayChunk(Base):
    __tablename__ = "essay_chunks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    chunk_index = Column(Integer, index=True)
    chunk_text = Column(Text, default="")
    chunk_summary = Column(Text, default="")
    chunk_terms = Column(Text, default="")
    chunk_hash = Column(String(64), default="")
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    # Relationship
    project = relationship("Project", back_populates="essay_chunks")
