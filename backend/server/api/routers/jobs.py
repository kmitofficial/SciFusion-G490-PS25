# Location: backend/server/api/routers/jobs.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, Query
from pydantic_mongo import PydanticObjectId
from typing import List, Optional, Literal
from pathlib import Path
from pydantic import BaseModel

from server.models.user import User
# --- FIX: Import our new model ---
from server.models.job import ResearchRequest, Job, JobSidebarItem
# --- END FIX ---
from server.services.auth import get_current_user
from server.services import research
from server.core.db import db
from motor.motor_asyncio import AsyncIOMotorCollection
from server.core.config import settings

router = APIRouter()
jobs_collection: AsyncIOMotorCollection = db.get_jobs_collection_async()


class ArtifactFolder(BaseModel):
    idea_name: Optional[str] = None
    idea_title: Optional[str] = None
    folder_name: str
    folder_path: str
    is_root: bool = False


class ArtifactNode(BaseModel):
    name: str
    path: str
    type: Literal["file", "directory"]
    children: Optional[List["ArtifactNode"]] = None


ArtifactNode.model_rebuild()


class ArtifactFile(BaseModel):
    path: str
    content: str


def _safe_resolve_path(base: Path, target: Path) -> Path:
    resolved_base = base.resolve()
    resolved_target = target.resolve()
    if resolved_base not in resolved_target.parents and resolved_base != resolved_target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested path is outside the allowed directory."
        )
    return resolved_target


def _resolve_folder_path(job_doc: dict, job_id: str, folder_identifier: str) -> Optional[Path]:
    results_dir = Path(settings.RESULTS_DIR)
    sample_dir = Path(settings.RESULTS_SAMPLE_DIR)
    print("inside resolve folder path function in jobs.py", results_dir)
    print("inside resolve folder path function in jobs.py", sample_dir)
    request_section = job_doc.get("request", {})
    save_name = request_section.get("save_name") if isinstance(request_section, dict) else getattr(request_section, "save_name", None)

    normalized_identifier = (folder_identifier or "").strip().strip("/")
    if not normalized_identifier:
        return None

    identifier_path = Path(normalized_identifier)

    candidate_paths: List[Path] = []
    seen: set[Path] = set()

    def add_candidate(path: Path):
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidate_paths.append(path)

    # Prefer direct relative path resolution if identifier includes subfolders
    if len(identifier_path.parts) > 1:
        add_candidate(results_dir / identifier_path)
        add_candidate(sample_dir / identifier_path)

    leaf_name = identifier_path.name

    if save_name:
        add_candidate(results_dir / save_name / leaf_name)
        add_candidate(sample_dir / save_name / leaf_name)

    job_folder = f"api_job_{job_id}"
    add_candidate(results_dir / job_folder / leaf_name)
    add_candidate(sample_dir / job_folder / leaf_name)

    if "_run_" in leaf_name:
        base_part, _, run_suffix = leaf_name.partition("_run_")
        if base_part and run_suffix:
            run_folder_name = f"run_{run_suffix}"
            add_candidate(results_dir / job_folder / base_part / run_folder_name)
            add_candidate(sample_dir / job_folder / base_part / run_folder_name)
            if save_name:
                add_candidate(results_dir / save_name / base_part / run_folder_name)
                add_candidate(sample_dir / save_name / base_part / run_folder_name)

    add_candidate(results_dir / identifier_path)
    add_candidate(sample_dir / identifier_path)
    add_candidate(sample_dir / "userResult" / leaf_name)

    for candidate in candidate_paths:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return None


def _path_to_identifier(path: Path, results_dir: Path, sample_dir: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(results_dir.resolve()).as_posix()
    except ValueError:
        pass

    try:
        return path.resolve().relative_to(sample_dir.resolve()).as_posix()
    except ValueError:
        pass

    return None


def _build_tree(root: Path, base: Path) -> List[ArtifactNode]:
    entries: List[ArtifactNode] = []
    try:
        children = sorted(list(root.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
    except (FileNotFoundError, PermissionError):
        return entries

    for child in children:
        rel_path = child.relative_to(base).as_posix()
        if child.is_dir():
            entries.append(
                ArtifactNode(
                    name=child.name,
                    path=rel_path,
                    type="directory",
                    children=_build_tree(child, base)
                )
            )
        else:
            entries.append(
                ArtifactNode(
                    name=child.name,
                    path=rel_path,
                    type="file"
                )
            )

    return entries


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED
)
async def create_new_job(
        request: ResearchRequest,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user)
):
    # ... (this function is correct, no changes needed) ...
    try:
        new_job = Job(
            request=request,
            status="pending",
            user_id=current_user.id
        )
        insert_result = await jobs_collection.insert_one(
            new_job.model_dump(by_alias=True)
        )
        job_id = str(insert_result.inserted_id)
        background_tasks.add_task(research.run_research_task, job_id, request)
        return {"job_id": job_id}

    except Exception as e:
        print(f"Failed to create job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start job: {str(e)}"
        )


@router.get(
    "/",
    # --- FIX: Change the response_model ---
    response_model=List[JobSidebarItem]
    # --- END FIX ---
)
async def get_all_jobs(
        current_user: User = Depends(get_current_user),
):
    """
    Gets all jobs for the currently authenticated user.
    Returns a list of JobSidebarItem objects.
    """
    jobs = []
    cursor = jobs_collection.find(
        {"user_id": current_user.id},
        # This projection now perfectly matches our new model
        {
            "request.topic": 1,
            "created_at": 1,
            "status": 1
            # _id is included by default
        }
    ).sort("created_at", -1)

    async for job_doc in cursor:
        # --- FIX: Validate against the new model ---
        jobs.append(JobSidebarItem(**job_doc))
        # --- END FIX ---

    return jobs


@router.get(
    "/{job_id}",
    response_model=Job
)
async def get_single_job(
        job_id: PydanticObjectId,
        current_user: User = Depends(get_current_user),
):
    # ... (this function is correct, no changes needed) ...
    job_doc = await jobs_collection.find_one(
        {"_id": job_id, "user_id": current_user.id}
    )

    if job_doc:
        return Job(**job_doc)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Job {job_id} not found or you do not have permission to view it."
    )


@router.get(
    "/{job_id}/artifacts/list",
    response_model=List[ArtifactFolder]
)
async def list_job_artifacts(
        job_id: PydanticObjectId,
        current_user: User = Depends(get_current_user),
):
    job_doc = await jobs_collection.find_one(
        {"_id": job_id, "user_id": current_user.id}
    )

    print("inside list_job_artifacts", job_doc)

    if not job_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or you do not have permission to view it."
        )

    job_id_str = str(job_id)
    experiment_results = job_doc.get("experiment_results", []) or []

    results_dir = Path(settings.RESULTS_DIR)
    sample_dir = Path(settings.RESULTS_SAMPLE_DIR)

    seen_folders = set()
    folders: List[ArtifactFolder] = []

    request_section = job_doc.get("request", {})
    save_name = request_section.get("save_name") if isinstance(request_section, dict) else getattr(request_section, "save_name", None)

    root_candidates: List[Path] = []
    if save_name:
        root_candidates.append(results_dir / save_name)
        root_candidates.append(sample_dir / save_name)

    root_candidates.append(results_dir / f"api_job_{job_id_str}")
    root_candidates.append(sample_dir / f"api_job_{job_id_str}")

    for candidate in root_candidates:
        if not candidate.exists() or not candidate.is_dir():
            continue

        identifier = _path_to_identifier(candidate, results_dir, sample_dir)
        if not identifier or identifier in seen_folders:
            continue

        seen_folders.add(identifier)
        folders.append(
            ArtifactFolder(
                folder_name="All artifacts",
                folder_path=identifier,
                is_root=True
            )
        )
        break

    for result in experiment_results:
        print("experiment results:", experiment_results)
        folder_name = result.get("folder_name")
        results_path = result.get("results_path")

        identifier = results_path or folder_name
        if not identifier or identifier in seen_folders:
            continue

        resolved = _resolve_folder_path(job_doc, job_id_str, identifier)
        if not resolved:
            continue

        seen_folders.add(identifier)
        display_name = folder_name or Path(identifier).name
        folder_path_value = results_path or Path(identifier).as_posix()
        folders.append(
            ArtifactFolder(
                idea_name=result.get("idea_name"),
                idea_title=result.get("idea_title"),
                folder_name=display_name,
                folder_path=folder_path_value
            )
        )

    return folders


@router.get(
    "/{job_id}/artifacts/tree",
    response_model=ArtifactNode
)
async def get_artifact_tree(
        job_id: PydanticObjectId,
        folder: str = Query(..., description="Folder name from experiment results"),
        current_user: User = Depends(get_current_user),
):
    job_doc = await jobs_collection.find_one(
        {"_id": job_id, "user_id": current_user.id}
    )

    if not job_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or you do not have permission to view it."
        )

    job_id_str = str(job_id)
    base_path = _resolve_folder_path(job_doc, job_id_str, folder)
    if not base_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifacts for folder '{folder}' could not be located."
        )

    tree_children = _build_tree(base_path, base_path)

    return ArtifactNode(
        name=base_path.name,
        path="",
        type="directory",
        children=tree_children
    )


@router.get(
    "/{job_id}/artifacts/file",
    response_model=ArtifactFile
)
async def get_artifact_file(
        job_id: PydanticObjectId,
        folder: str = Query(..., description="Folder name from experiment results"),
        file_path: str = Query(..., alias="path", description="Relative path to the file"),
        current_user: User = Depends(get_current_user),
):
    job_doc = await jobs_collection.find_one(
        {"_id": job_id, "user_id": current_user.id}
    )

    if not job_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or you do not have permission to view it."
        )

    job_id_str = str(job_id)
    base_path = _resolve_folder_path(job_doc, job_id_str, folder)
    if not base_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifacts for folder '{folder}' could not be located."
        )

    target = _safe_resolve_path(base_path, base_path / file_path)

    if not target.exists() or not target.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file was not found."
        )

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {exc}"
        ) from exc

    rel_path = target.relative_to(base_path).as_posix()
    return ArtifactFile(path=rel_path, content=content)