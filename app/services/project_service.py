from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models


def list_projects(db: Session, owner_id: str, limit: int = 20, offset: int = 0):
    return (
        db.query(models.Project)
        .filter(models.Project.owner_id == owner_id)
        .order_by(models.Project.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def create_project(db: Session, title: str, owner_id: str) -> models.Project:
    db_project = models.Project(title=title, owner_id=owner_id)
    db.add(db_project)
    db.flush()
    db.add(models.Document(project_id=db_project.id, content=""))
    db.add(models.EssayMemory(project_id=db_project.id, thesis="", memory_notes="", chunk_count=0, document_hash=""))
    db.commit()
    db.refresh(db_project)
    return db_project


def get_owned_project_or_404(db: Session, project_id: int, owner_id: str) -> models.Project:
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id, models.Project.owner_id == owner_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project
