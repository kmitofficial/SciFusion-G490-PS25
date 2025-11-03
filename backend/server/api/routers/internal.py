from fastapi import APIRouter, HTTPException, Body
from server.core.db import db
from server.services.websocket import manager
from server.models.job import Job
from pydantic_mongo import PydanticObjectId
from typing import Dict, Any, List

router = APIRouter()
jobs_collection = db.get_jobs_collection_async()


async def get_job_and_user_id(job_id: str):
    """Helper to find a job and its owner's user_id."""
    try:
        job_oid = PydanticObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Job ID format")

    job_doc = await jobs_collection.find_one({"_id": job_oid})

    if not job_doc:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return job_doc, str(job_doc["user_id"])


async def notify_user_of_update(job_id: str):
    """
    Finds a job, finds its owner, and sends them
    the full updated job document over WebSocket.
    """
    job_doc, user_id = await get_job_and_user_id(job_id)

    # Send the full, updated job to the user
    message = {
        "type": "JOB_UPDATE",
        "data": Job(**job_doc).model_dump(mode="json")
    }
    await manager.send_json(user_id, message)


@router.post("/_internal/update-job-status/{job_id}", tags=["_Internal"])
async def internal_update_job_status(job_id: str, status: str = Body(..., embed=True)):
    """Called by the script to update the job's high-level status."""

    print(f"[Internal API] Job {job_id} status changed to: {status}")

    job_doc, user_id = await get_job_and_user_id(job_id)

    await jobs_collection.update_one(
        {"_id": job_doc["_id"]},
        {"$set": {"status": status}}
    )

    await notify_user_of_update(job_id)
    return {"message": "Status updated"}


@router.post("/_internal/update-papers/{job_id}", tags=["_Internal"])
async def internal_update_papers(job_id: str, papers: Dict[str, Any] = Body(...)):
    """Called by the script when papers are found."""

    print(f"[Internal API] Job {job_id} received papers.")

    job_doc, user_id = await get_job_and_user_id(job_id)

    await jobs_collection.update_one(
        {"_id": job_doc["_id"]},
        {"$set": {"papers": papers, "status": "papers_collected"}}
    )

    await notify_user_of_update(job_id)
    return {"message": "Papers updated"}


@router.post("/_internal/update-ideas/{job_id}", tags=["_Internal"])
async def internal_update_ideas(job_id: str, ideas: List[Dict[str, Any]] = Body(...)):
    """Called by the script when ideas are generated."""

    print(f"[Internal API] Job {job_id} received ideas.")

    job_doc, user_id = await get_job_and_user_id(job_id)

    await jobs_collection.update_one(
        {"_id": job_doc["_id"]},
        {"$set": {"ideas": ideas, "status": "ideas_generated"}}
    )

    await notify_user_of_update(job_id)
    return {"message": "Ideas updated"}


@router.post("/_internal/push-result/{job_id}", tags=["_Internal"])
async def internal_push_experiment_result(job_id: str, result: Dict[str, Any] = Body(...)):
    """Called by the script after *each* experiment."""

    print(f"[Internal API] Job {job_id} received an experiment result.")

    job_doc, user_id = await get_job_and_user_id(job_id)

    await jobs_collection.update_one(
        {"_id": job_doc["_id"]},
        {"$push": {"experiment_results": result}, "$set": {"status": "experiments_running"}}
    )

    await notify_user_of_update(job_id)
    return {"message": "Result pushed"}