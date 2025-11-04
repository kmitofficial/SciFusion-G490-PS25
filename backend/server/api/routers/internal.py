from fastapi import APIRouter, Depends, Body
from server.services.websocket import manager  # <-- Import the manager
from server.services.auth import get_current_user_stub
from server.models.user import User
from server.core.db import db
from bson import ObjectId
from typing import List, Dict, Any

router = APIRouter()
jobs_collection = db.get_jobs_collection_async()


# --- NEW: Helper function ---
async def get_user_id_for_job(job_id: str) -> str | None:
    """Finds the user_id associated with a given job_id."""
    try:
        # Ensure job_id is a valid ObjectId
        if not ObjectId.is_valid(job_id):
            print(f"Invalid job_id format: {job_id}")
            return None

        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
        if job and "user_id" in job:
            return str(job["user_id"])
    except Exception as e:
        print(f"Error finding user for job {job_id}: {e}")
    return None


@router.post("/_internal/update-job-status/{job_id}")
async def update_job_status(job_id: str, status_data: Dict[str, str] = Body(...)):
    status = status_data.get("status", "unknown")
    await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"status": status}}
    )

    # --- WebSocket Push ---
    user_id = await get_user_id_for_job(job_id)
    if user_id:
        await manager.send_json(user_id, {
            "type": "JOB_STATUS_UPDATE",
            "data": {"status": status}
        })
    return {"message": "Status updated"}


@router.post("/_internal/update-papers/{job_id}")
async def update_papers(job_id: str, papers_data: Dict[str, Any] = Body(...)):
    await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"papers": papers_data}}
    )

    # --- WebSocket Push ---
    user_id = await get_user_id_for_job(job_id)
    if user_id:
        await manager.send_json(user_id, {
            "type": "PAPERS_UPDATED",
            "data": papers_data
        })
    return {"message": "Papers updated"}


@router.post("/_internal/update-ideas/{job_id}")
async def update_ideas(job_id: str, ideas_list: List[Dict[str, Any]] = Body(...)):
    await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"ideas": ideas_list}}
    )

    # --- WebSocket Push ---
    user_id = await get_user_id_for_job(job_id)
    if user_id:
        await manager.send_json(user_id, {
            "type": "IDEAS_UPDATED",
            "data": ideas_list
        })
    return {"message": "Ideas updated"}


@router.post("/_internal/update-novel-ideas/{job_id}")
async def update_novel_ideas(job_id: str, ideas_list: List[Dict[str, Any]] = Body(...)):
    """
    Receives the FINAL list of novel ideas that will be run.
    This is used to set the 'total' for the progress bar.
    """
    # We don't necessarily need to save this to the DB,
    # but we MUST broadcast it.

    # --- WebSocket Push ---
    user_id = await get_user_id_for_job(job_id)
    if user_id:
        await manager.send_json(user_id, {
            "type": "NOVEL_IDEAS_UPDATED",
            "data": ideas_list
        })
    return {"message": "Novel ideas list broadcasted"}


@router.post("/_internal/push-result/{job_id}")
async def push_experiment_result(job_id: str, result_data: Dict[str, Any] = Body(...)):
    await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$push": {"experiment_results": result_data}}
    )

    # --- WebSocket Push ---
    user_id = await get_user_id_for_job(job_id)
    if user_id:
        await manager.send_json(user_id, {
            "type": "EXPERIMENT_RESULT",
            "data": result_data
        })
    return {"message": "Result pushed"}


# --- NEW ENDPOINT ---
@router.post("/_internal/push-log/{job_id}")
async def push_log_message(job_id: str, log_data: Dict[str, str] = Body(...)):
    # You could optionally save logs to the DB here if you want
    # await jobs_collection.update_one(
    #     {"_id": ObjectId(job_id)},
    #     {"$push": {"log_feed": log_data}}
    # )

    # --- WebSocket Push ---
    user_id = await get_user_id_for_job(job_id)
    if user_id:
        await manager.send_json(user_id, {
            "type": "AIDER_LOG",
            "data": log_data  # This contains {"message": "...", "log_type": "info"}
        })
    return {"message": "Log pushed"}
