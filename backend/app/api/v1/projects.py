"""
Projects API endpoints
Gestión de proyectos para organizar imágenes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.image import Image
from app.schemas.image import ImageResponse
from app.api.deps import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    user_id: str
    created_at: str
    updated_at: str
    image_count: int

    class Config:
        from_attributes = True


# ── Helpers ────────────────────────────────────────────────────────────────


def _project_to_response(project: Project, db: Session) -> dict:
    image_count = db.query(Image).filter(Image.project_id == project.id).count()
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description or "",
        "user_id": project.user_id,
        "created_at": project.created_at.isoformat() if project.created_at else "",
        "updated_at": project.updated_at.isoformat() if project.updated_at else "",
        "image_count": image_count,
    }


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crear nuevo proyecto"""
    existing = (
        db.query(Project)
        .filter(Project.user_id == current_user.id, Project.name == project_data.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un proyecto con el nombre '{project_data.name}'",
        )

    project = Project(
        name=project_data.name,
        description=project_data.description,
        user_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info(f"Project created: {project.id} ({project.name})")
    return _project_to_response(project, db)


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Listar proyectos del usuario actual"""
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_project_to_response(p, db) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Obtener detalles de un proyecto"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return _project_to_response(project, db)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Actualizar nombre o descripción de proyecto"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    if project.name == "default":
        raise HTTPException(
            status_code=400, detail="No se puede editar el proyecto 'default'"
        )

    if project_data.name is not None:
        existing = (
            db.query(Project)
            .filter(
                Project.user_id == current_user.id,
                Project.name == project_data.name,
                Project.id != project_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un proyecto con el nombre '{project_data.name}'",
            )
        project.name = project_data.name

    if project_data.description is not None:
        project.description = project_data.description

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    logger.info(f"Project updated: {project.id} ({project.name})")
    return _project_to_response(project, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Eliminar proyecto (cascade elimina imágenes asociadas)"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    if project.name == "default":
        raise HTTPException(
            status_code=400, detail="No se puede eliminar el proyecto 'default'"
        )

    db.delete(project)
    db.commit()
    logger.info(f"Project deleted: {project_id}")
    return None


@router.get("/{project_id}/images", response_model=List[ImageResponse])
def get_project_images(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Listar imágenes de un proyecto"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    images = (
        db.query(Image)
        .filter(Image.project_id == project_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return images
