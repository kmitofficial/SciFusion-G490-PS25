"""REST endpoints for managing AutoAD experiment scaffolds."""
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models.project import (
    ProjectCreateRequest,
    ProjectDetail,
    ProjectResponse,
    ProjectSummary,
)
from app.services import project_service
from app.services.project_service import (
    ProjectExistsError,
    ProjectNotFoundError,
)

router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new AutoAD project scaffold",
)
async def create_project(payload: ProjectCreateRequest) -> ProjectResponse:
    """Provision a new experiment directory and return its metadata."""
    try:
        detail = project_service.create_project(payload)
    except ProjectExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return ProjectResponse(message="Project scaffold created", project=detail)


@router.get(
    "",
    response_model=List[ProjectSummary],
    summary="List all scaffolded projects",
)
async def list_projects() -> List[ProjectSummary]:
    """Return a reverse-chronological listing of provisioned projects."""
    return project_service.list_projects()


@router.get(
    "/{slug}",
    response_model=ProjectDetail,
    summary="Fetch a single project configuration",
)
async def get_project(slug: str) -> ProjectDetail:
    """Fetch persisted configuration for an existing project."""
    try:
        return project_service.get_project(slug)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
