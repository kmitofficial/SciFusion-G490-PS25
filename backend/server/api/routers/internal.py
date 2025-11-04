# Location: backend/server/api/routers/internal.py

from fastapi import APIRouter, Depends, Body, Path, HTTPException, status, Request
from pydantic_mongo import PydanticObjectId
from typing import Dict, Any, List

from server.models.user import User
from server.services.auth import get_current_user
from server.services.websocket import manager
from server.core.db import db
from motor.motor_asyncio import AsyncIOMotorCollection

router = APIRouter(
    prefix="/_internal",
    tags=["_Internal"],
    include_in_schema=False
)

jobs_collection: AsyncIOMotorCollection = db.get_jobs_collection_async()


async def get_job_and_user_id(job_id: PydanticObjectId) -> str:
    """Helper to find the user_id for a given job_id."""
    job_doc = await jobs_collection.find_one(
        {"_id": job_id},
        {"user_id": 1}
    )
    if not job_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return str(job_doc["user_id"])


@router.post("/update-job-status/{job_id}")
async def update_job_status(
        job_id: PydanticObjectId,
        status: str = Body(..., embed=True),
):
    """
    Internal endpoint for the research script to update its own status.
    """
    user_id = await get_job_and_user_id(job_id)
    await jobs_collection.update_one(
        {"_id": job_id},
        {"$set": {"status": status}}
    )
    await manager.send_json(user_id, {
        "type": "JOB_STATUS_UPDATE",
        "data": {"status": status, "job_id": str(job_id)}
    })
    return {"status": "ok", "job_id": str(job_id), "new_status": status}


@router.post("/push-log/{job_id}")
async def push_log(
        job_id: PydanticObjectId,
        request: Request
):
    """
    Internal endpoint for the research script to send a log message.
    This now accepts any valid JSON and figures out what to do.
    """
    user_id = await get_job_and_user_id(job_id)

    try:
        data = await request.json()
    except Exception as e:
        print(f"--- LOG PARSE ERROR ---: Could not parse log body: {e}")
        await manager.send_json(user_id, {
            "type": "AIDER_LOG",
            "data": {"message": f"!!! FAILED TO PARSE LOG: {e} !!!", "log_type": "error"}
        })
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    log_message = ""
    if isinstance(data, str):
        log_message = data
    elif isinstance(data, dict) and "message" in data:
        log_message = data["message"]
    elif isinstance(data, dict) and "log_message" in data:
        log_message = data["log_message"]
    elif isinstance(data, dict) and "log" in data:
        log_message = data["log"]
    else:
        log_message = f"[UNRECOGNIZED LOG FORMAT]: {str(data)}"

    log_type = "info"
    if "error" in log_message.lower():
        log_type = "error"
    elif "fail" in log_message.lower():
        log_type = "fail"
    elif "success" in log_message.lower():
        log_type = "success"

    await manager.send_json(user_id, {
        "type": "AIDER_LOG",
        "data": {
            "message": log_message,
            "log_type": log_type
        }
    })
    return {"status": "log pushed"}


@router.post("/update-papers/{job_id}")
async def update_papers(
        job_id: PydanticObjectId,
        papers_data: Dict[str, Any] = Body(...)
):
    """
    Internal endpoint for the research script to post the paper bank.
    """
    user_id = await get_job_and_user_id(job_id)
    await jobs_collection.update_one(
        {"_id": job_id},
        {"$set": {"papers": papers_data}}
    )
    await manager.send_json(user_id, {
        "type": "PAPERS_UPDATED",
        "data": papers_data
    })
    return {"status": "papers updated"}


# --- FIX: Renamed route from '/update-ideas' to '/update-novel-ideas' ---
@router.post("/update-novel-ideas/{job_id}")
async def update_novel_ideas(
        job_id: PydanticObjectId,
        ideas_data: List[Dict[str, Any]] = Body(...)
):
    # --- END FIX ---
    """
    Internal endpoint for the research script to post the novel ideas.
    (This is the FINAL list of ideas to be run)
    """
    user_id = await get_job_and_user_id(job_id)

    # 1. Update the DB
    await jobs_collection.update_one(
        {"_id": job_id},
        {"$set": {"ideas": ideas_data}}
    )

    # 2. Push to client
    await manager.send_json(user_id, {
        "type": "NOVEL_IDEAS_UPDATED",
        "data": ideas_data
    })
    return {"status": "novel ideas updated"}


# --- FIX: Renamed route from '/push-experiment-result' to '/push-result' ---
@router.post("/push-result/{job_id}")
async def push_result(
        job_id: PydanticObjectId,
        result_data: Dict[str, Any] = Body(...)
):
    # --- END FIX ---
    """
    Internal endpoint for the research script to post a SINGLE run result.
    The body is expected to be the ExperimentResult object.
    """
    user_id = await get_job_and_user_id(job_id)

    # 1. Push this single result to the 'experiment_results' array in DB
    await jobs_collection.update_one(
        {"_id": job_id},
        {"$push": {"experiment_results": result_data}}
    )

    # 2. Push to client
    await manager.send_json(user_id, {
        "type": "EXPERIMENT_RESULT",
        "data": result_data
    })
    return {"status": "result pushed"}