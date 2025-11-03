from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends
from server.services import research
from server.models.job import ResearchRequest, Job
from server.models.user import User  # To type-hint our user
from server.core.db import db
from server.services.auth import get_current_user_stub  # <-- OUR DUMMY AUTH!
from pydantic_mongo import PydanticObjectId
from typing import List

router = APIRouter()
jobs_collection = db.get_jobs_collection_async()


@router.post("/", response_model=Job, status_code=status.HTTP_201_CREATED, tags=["Jobs"])
async def create_job(
        req: ResearchRequest,
        background_tasks: BackgroundTasks,
        # This 'Depends' runs our dummy auth function and gives
        # us the 'testuser' object.
        current_user: User = Depends(get_current_user_stub)
):
    """
    Creates a new research job, linked to our stub user.
    """

    # Create the job, now linking it to the logged-in user
    new_job = Job(request=req, status="pending", user_id=current_user.id)

    insert_result = await jobs_collection.insert_one(
        new_job.model_dump(by_alias=True)
    )
    job_id = str(insert_result.inserted_id)

    background_tasks.add_task(research.run_research_task, job_id, req)

    created_job_doc = await jobs_collection.find_one(
        {"_id": insert_result.inserted_id}
    )
    if created_job_doc:
        return Job(**created_job_doc)
    raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/{job_id}", response_model=Job, tags=["Jobs"])
async def get_job_status(
        job_id: str,
        current_user: User = Depends(get_current_user_stub)
):
    """
    Gets the status for a *specific* job.
    Checks that the job belongs to our stub user.
    """
    try:
        job_oid = PydanticObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Job ID format")

    job_doc = await jobs_collection.find_one({"_id": job_oid})

    if not job_doc:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Check if the job's user_id matches the current user's id
    if job_doc["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    return Job(**job_doc)


@router.get("/", response_model=List[Job], tags=["Jobs"])
async def get_all_jobs_for_user(
        current_user: User = Depends(get_current_user_stub)
):
    """
    Gets a list of all jobs created by our stub user.
    """
    jobs_cursor = jobs_collection.find({"user_id": current_user.id})
    jobs_list = await jobs_cursor.to_list(length=100)
    return [Job(**job) for job in jobs_list]