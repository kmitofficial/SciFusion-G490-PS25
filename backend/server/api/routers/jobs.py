# Location: backend/server/api/routers/jobs.py
import io
import zipfile
import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic_mongo import PydanticObjectId
from typing import List, Optional, Literal, Dict, Any
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime
from server.models.user import User
from server.models.job import ResearchRequest, Job, JobSidebarItem
from server.services.auth import get_current_user
from server.services import research
from server.core.db import db
from motor.motor_asyncio import AsyncIOMotorCollection
from server.core.config import settings
from enum import Enum

# --- Job Status Enum ---
class JobStatus(str, Enum):
    PENDING = "pending"
    PAPERS_COLLECTED = "papers_collected"
    PENDING_HUMAN_PAPERS = "pending_human_papers"
    PAPERS_REVIEWED = "papers_reviewed"
    IDEAS_GENERATED = "ideas_generated"
    PENDING_HUMAN_IDEA = "pending_human_idea"
    CODE_GENERATED = "code_generated"
    PENDING_HUMAN_CODE = "pending_human_code"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# --- WebSocket Manager ---
try:
    from server.services.websocket import manager
except ImportError:
    class DummyManager:
        async def broadcast(self, *args, **kwargs):
            pass
    manager = DummyManager()

router = APIRouter()
jobs_collection: AsyncIOMotorCollection = db.get_jobs_collection_async()

# --- Helper to broadcast status ---
async def _broadcast_status(job_id: str, status: str, extra: Dict[str, Any] = None):
    payload = {"type": "JOB_STATUS_UPDATE", "data": {"status": status, **(extra or {})}}
    await manager.broadcast(payload, job_id)


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


class PaperSelectionRequest(BaseModel):
    selected_paper_ids: Optional[List[str]] = None
    comment: Optional[str] = None
    skip: bool = False


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


@router.post("/{job_id}/paper-review")
async def submit_paper_review(
    job_id: PydanticObjectId,
    payload: PaperSelectionRequest,
    current_user: User = Depends(get_current_user)
):
    job = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    current_status = str(job.get("status") or "")
    allowed_statuses = {JobStatus.PENDING_HUMAN_PAPERS.value, JobStatus.RUNNING.value}
    if current_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Job is not awaiting paper review")

    if job.get("paper_review") and current_status != JobStatus.PENDING_HUMAN_PAPERS.value:
        raise HTTPException(status_code=400, detail="Paper review already submitted")

    selected_ids = payload.selected_paper_ids or []
    if not payload.skip and not selected_ids and not (payload.comment and payload.comment.strip()):
        raise HTTPException(status_code=400, detail="Select papers, add a comment, or choose skip.")

    papers_bank = ((job.get("papers") or {}).get("paper_bank")) or []
    selected_papers = [paper for paper in papers_bank if paper.get("id") in selected_ids]

    review_doc = {
        "selected_paper_ids": selected_ids,
        "selected_papers": selected_papers,
        "comment": payload.comment.strip() if payload.comment else None,
        "skip": payload.skip,
        "submitted_at": datetime.utcnow().isoformat() + "Z",
    }

    await jobs_collection.update_one(
        {"_id": job_id},
        {"$set": {"paper_review": review_doc, "status": JobStatus.PAPERS_REVIEWED}}
    )

    await _broadcast_status(str(job_id), JobStatus.PAPERS_REVIEWED, extra={"paper_review": review_doc})
    return {"status": "paper_review_recorded"}


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_new_job(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    try:
        new_job = Job(
            request=request,
            status=JobStatus.PENDING,
            user_id=current_user.id,
            requires_human=True,
            current_idea_idx=0,
            ideas=[],
            experiment_results=[]
        )
        insert_result = await jobs_collection.insert_one(new_job.model_dump(by_alias=True))
        job_id = str(insert_result.inserted_id)
        background_tasks.add_task(research.run_research_task, job_id, request)
        return {"job_id": job_id}
    except Exception as e:
        print(f"Failed to create job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start job: {str(e)}"
        )


@router.get("/", response_model=List[JobSidebarItem])
async def get_all_jobs(current_user: User = Depends(get_current_user)):
    jobs = []
    cursor = jobs_collection.find(
        {"user_id": current_user.id},
        {"request.topic": 1, "created_at": 1, "status": 1}
    ).sort("created_at", -1)
    async for job_doc in cursor:
        jobs.append(JobSidebarItem(**job_doc))
    return jobs


@router.get("/{job_id}", response_model=Job)
async def get_single_job(
    job_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    job_doc = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if job_doc:
        return Job(**job_doc)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Job {job_id} not found or you do not have permission to view it."
    )


# --- HITL ENDPOINTS ---

@router.post("/{job_id}/approve-idea")
async def approve_idea(
    job_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    job = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if not job or job["status"] != JobStatus.PENDING_HUMAN_IDEA:
        raise HTTPException(status_code=400, detail="Idea not pending approval")

    await jobs_collection.update_one(
        {"_id": job_id},
        {"$set": {"status": JobStatus.CODE_GENERATED}}
    )
    await _broadcast_status(str(job_id), JobStatus.CODE_GENERATED)
    from server.services.research import generate_code_for_idea
    asyncio.create_task(generate_code_for_idea(str(job_id)))
    return {"status": "code_generation_started"}


@router.post("/{job_id}/approve-code")
async def approve_code(
    job_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    job = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if not job or job["status"] != JobStatus.PENDING_HUMAN_CODE:
        raise HTTPException(status_code=400, detail="Code not pending approval")

    await jobs_collection.update_one(
        {"_id": job_id},
        {"$set": {"status": JobStatus.RUNNING}}
    )
    await _broadcast_status(str(job_id), JobStatus.RUNNING)
    from server.services.research import run_experiment
    asyncio.create_task(run_experiment(str(job_id)))
    return {"status": "experiment_started"}


@router.post("/{job_id}/submit-feedback")
async def submit_feedback(
    job_id: PydanticObjectId,
    feedback: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    job = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Save feedback
    await jobs_collection.update_one(
        {"_id": job_id},
        {"$set": {"human_feedback": feedback}}
    )
    await _broadcast_status(str(job_id), job["status"], extra={"feedback": feedback})

    # Trigger next idea if in RUNNING state
    if job["status"] == JobStatus.RUNNING and job.get("current_idea_idx", 0) < len(job.get("ideas", [])):
        from server.services.research import generate_next_idea_with_feedback
        asyncio.create_task(generate_next_idea_with_feedback(str(job_id)))

    return {"status": "feedback_received"}


# --- Artifact Endpoints (unchanged) ---

@router.get("/{job_id}/artifacts/list", response_model=List[ArtifactFolder])
async def list_job_artifacts(
    job_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    job_doc = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
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
        folders.append(ArtifactFolder(folder_name="All artifacts", folder_path=identifier, is_root=True))
        break

    for result in experiment_results:
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


@router.get("/{job_id}/artifacts/tree", response_model=ArtifactNode)
async def get_artifact_tree(
    job_id: PydanticObjectId,
    folder: str = Query(..., description="Folder name from experiment results"),
    current_user: User = Depends(get_current_user),
):
    job_doc = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    job_id_str = str(job_id)
    base_path = _resolve_folder_path(job_doc, job_id_str, folder)
    if not base_path:
        raise HTTPException(status_code=404, detail=f"Artifacts for folder '{folder}' could not be located.")
    tree_children = _build_tree(base_path, base_path)
    return ArtifactNode(name=base_path.name, path="", type="directory", children=tree_children)


@router.get("/{job_id}/artifacts/file", response_model=ArtifactFile)
async def get_artifact_file(
    job_id: PydanticObjectId,
    folder: str = Query(..., description="Folder name from experiment results"),
    file_path: str = Query(..., alias="path", description="Relative path to the file"),
    current_user: User = Depends(get_current_user),
):
    job_doc = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    job_id_str = str(job_id)
    base_path = _resolve_folder_path(job_doc, job_id_str, folder)
    if not base_path:
        raise HTTPException(status_code=404, detail=f"Artifacts for folder '{folder}' could not be located.")
    target = _safe_resolve_path(base_path, base_path / file_path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Requested file was not found.")
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {exc}") from exc
    rel_path = target.relative_to(base_path).as_posix()
    return ArtifactFile(path=rel_path, content=content)


@router.get("/{job_id}/artifacts/download")
async def download_artifact_folder(
    job_id: PydanticObjectId,
    folder: str = Query(..., description="Folder identifier to download"),
    current_user: User = Depends(get_current_user),
):
    job_doc = await jobs_collection.find_one({"_id": job_id, "user_id": current_user.id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    job_id_str = str(job_id)
    base_path = _resolve_folder_path(job_doc, job_id_str, folder)
    if not base_path:
        raise HTTPException(status_code=404, detail=f"Artifacts for folder '{folder}' could not be located.")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in base_path.rglob("*"):
            arcname = file_path.relative_to(base_path).as_posix()
            if not arcname:
                continue
            if file_path.is_dir():
                zip_file.writestr(f"{arcname.rstrip('/')}/", "")
            else:
                zip_file.write(file_path, arcname)
    buffer.seek(0)
    filename = f"{base_path.name}.zip"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)