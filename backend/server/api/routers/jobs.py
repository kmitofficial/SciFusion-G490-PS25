# Location: backend/server/api/routers/jobs.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from pydantic_mongo import PydanticObjectId
from typing import List

from server.models.user import User
# --- FIX: Import our new model ---
from server.models.job import ResearchRequest, Job, JobSidebarItem
# --- END FIX ---
from server.services.auth import get_current_user
from server.services import research
from server.core.db import db
from motor.motor_asyncio import AsyncIOMotorCollection

router = APIRouter()
jobs_collection: AsyncIOMotorCollection = db.get_jobs_collection_async()


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