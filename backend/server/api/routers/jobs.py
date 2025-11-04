# Location: backend/server/api/routers/jobs.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from pydantic_mongo import PydanticObjectId

from server.models.user import User
from server.models.job import ResearchRequest, Job
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
    """
    Creates and starts a new research job for the authenticated user.
    """
    try:
        # 1. Create the job document
        new_job = Job(
            request=request,
            status="pending",
            user_id=current_user.id  # Link the job to the user
        )

        # 2. Insert into the database
        insert_result = await jobs_collection.insert_one(
            new_job.model_dump(by_alias=True)
        )
        job_id = str(insert_result.inserted_id)

        # 3. Add the research task to run in the background
        background_tasks.add_task(research.run_research_task, job_id, request)

        # 4. Return the new job ID to the client
        return {"job_id": job_id}

    except Exception as e:
        print(f"Failed to create job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start job: {str(e)}"
        )


@router.get("/")
async def get_all_jobs(
        current_user: User = Depends(get_current_user),
):
    """
    (Placeholder for Stage 4)
    Gets all jobs for the current user.
    """
    return {"message": f"Hello {current_user.username}, your jobs will be here in Stage 4."}