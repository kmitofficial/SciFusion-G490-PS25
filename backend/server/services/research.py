import subprocess
import sys
import os
import asyncio
from typing import Dict, Any, Optional, Coroutine
from server.models.job import ResearchRequest, Job
from server.core.db import db
from bson import ObjectId
from enum import Enum

# --- NEW: Job Status Enum ---
class JobStatus(str, Enum):
    PENDING = "pending"
    PAPERS_COLLECTED = "papers_collected"
    IDEAS_GENERATED = "ideas_generated"
    PENDING_HUMAN_IDEA = "pending_human_idea"
    CODE_GENERATED = "code_generated"
    PENDING_HUMAN_CODE = "pending_human_code"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# --- NEW: WebSocket Manager ---
try:
    from server.services.websocket import manager
except ImportError:
    async def manager_broadcast(*args, **kwargs):
        pass
    manager = type("Manager", (), {"broadcast": manager_broadcast})()

# Import the API callback functions from launch_dolphin
try:
    from launch_dolphin import update_job_status
except ImportError:
    def update_job_status(job_id, status):
        print(f"[RESEARCH_SERVICE] Fallback: Job {job_id} status to {status}")

# Get the synchronous 'jobs' collection
jobs_collection = db.get_jobs_collection_sync()


# --- NEW: Helper to broadcast status ---
async def _broadcast_status(job_id: str, status: str, extra: Dict[str, Any] = None):
    payload = {"type": "JOB_STATUS_UPDATE", "data": {"status": status, **(extra or {})}}
    await manager.broadcast(payload, job_id)
    update_job_status(job_id, status)


# --- NEW: Async helpers (called from endpoints) ---
async def generate_code_for_idea(job_id: str):
    job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        return

    # Simulate code generation (in real: call Aider or LLM)
    await asyncio.sleep(2)
    job["status"] = JobStatus.PENDING_HUMAN_CODE if job.get("requires_human", True) else JobStatus.RUNNING
    await jobs_collection.update_one({"_id": ObjectId(job_id)}, {"$set": {"status": job["status"]}})
    await _broadcast_status(job_id, job["status"])

    if not job.get("requires_human", True):
        asyncio.create_task(run_experiment(job_id))


async def run_experiment(job_id: str):
    job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        return

    # Simulate experiment run
    await asyncio.sleep(3)
    result = {
        "idea_name": job["ideas"][job["current_idea_idx"]]["Name"],
        "run_number": 1,
        "accuracy": 0.921,
        "folder_name": f"run_1",
        "results_path": f"api_job_{job_id}/run_1"
    }
    job["experiment_results"].append(result)
    job["current_idea_idx"] += 1

    if job["current_idea_idx"] < len(job["ideas"]):
        job["status"] = JobStatus.IDEAS_GENERATED
        asyncio.create_task(generate_next_idea_with_feedback(job_id))
    else:
        job["status"] = JobStatus.COMPLETED

    await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "status": job["status"],
            "experiment_results": job["experiment_results"],
            "current_idea_idx": job["current_idea_idx"]
        }}
    )
    await _broadcast_status(job_id, job["status"])


async def generate_next_idea_with_feedback(job_id: str):
    job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        return

    prev_result = job["experiment_results"][-1]
    feedback = job.get("human_feedback", {}).get("result", {})

    prompt_suffix = f"""
    Previous Result:
    - Idea: {prev_result['idea_name']}
    - Accuracy: {prev_result.get('accuracy', 'N/A')}
    - Human Label: {feedback.get('label', 'None')}
    - Human Comment: {feedback.get('comment', 'None')}

    Improve this idea. Be specific and actionable.
    """

    # In real: call LLM with prompt_suffix
    await asyncio.sleep(1)
    new_idea = {
        "Name": f"Improved Idea {job['current_idea_idx'] + 1}",
        "text": f"Use Transformer with focal loss and LoRA based on human feedback: '{feedback.get('comment', '')}'"
    }
    job["ideas"].append(new_idea)
    job["status"] = JobStatus.PENDING_HUMAN_IDEA if job.get("requires_human", True) else JobStatus.CODE_GENERATED

    await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"ideas": job["ideas"], "status": job["status"]}}
    )
    await _broadcast_status(job_id, job["status"])


# --- MAIN TASK: Modified to support HITL ---
def run_research_task(
    job_id: str,
    req: ResearchRequest,
    loop: Optional[asyncio.AbstractEventLoop] = None,
):
    """
    Background task with HITL pause points.
    """
    try:
        job_oid = ObjectId(job_id)
    except Exception:
        print(f"[Job: {job_id}] ERROR: Invalid Job ID format. Aborting.")
        return

    def _schedule(coro: Coroutine[Any, Any, Any]) -> None:
        """Safely execute a coroutine from this background thread."""
        if loop and loop.is_running():
            loop.call_soon_threadsafe(asyncio.create_task, coro)
        else:
            asyncio.run(coro)

    # --- Setup paths ---
    python_executable = sys.executable
    script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "launch_dolphin.py")
    )
    working_dir = os.path.dirname(script_path)

    print(f"--- [Job: {job_id}] Starting Job ---")

    # Build the command
    command = [
        python_executable, script_path,
        "--model", req.model,
        "--code_model", req.code_model,
        "--experiment", req.experiment,
        "--topic", req.topic,
        "--num-ideas", str(req.num_ideas),
        "--round", str(req.round),
        "--save_name", f"api_job_{job_id}",
        "--job-id", job_id
    ]

    if req.rag:
        command.append("--rag")
    if req.check_similarity:
        command.append("--check_similarity")
    if req.skip_novelty_check:
        command.append("--skip-novelty-check")

    print(f"[Job: {job_id}] Running command: {' '.join(command)}")

    final_log = ""
    final_error_log = ""

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=working_dir
        )

        final_log = process.stdout
        final_error_log = process.stderr

        if process.returncode == 0:
            print(f"--- [Job: {job_id}] launch_dolphin Finished ---")

            # --- HITL: After ideas generated ---
            job_update = {
                "log": final_log,
                "error_log": final_error_log,
                "status": JobStatus.IDEAS_GENERATED,
                "requires_human": req.rag,  # or add field to ResearchRequest
                "current_idea_idx": 0,
                "ideas": [],  # will be filled
                "experiment_results": []
            }
            jobs_collection.update_one({"_id": job_oid}, {"$set": job_update})

            # --- Pause for human if enabled ---
            if req.rag:  # using rag as proxy for HITL
                jobs_collection.update_one(
                    {"_id": job_oid},
                    {"$set": {"status": JobStatus.PENDING_HUMAN_IDEA}}
                )
                _schedule(_broadcast_status(job_id, JobStatus.PENDING_HUMAN_IDEA))
            else:
                # Auto-proceed
                _schedule(generate_code_for_idea(job_id))

        else:
            print(f"--- [Job: {job_id}] Script Failed (Return Code {process.returncode}) ---")
            jobs_collection.update_one(
                {"_id": job_oid},
                {"$set": {
                    "status": JobStatus.FAILED,
                    "log": final_log,
                    "error_log": final_error_log
                }}
            )
            _schedule(_broadcast_status(job_id, JobStatus.FAILED))

    except Exception as e:
        print(f"--- [Job: {job_id}] Script Host Failed Critically ---")
        final_error_log = str(e)
        jobs_collection.update_one(
            {"_id": job_oid},
            {"$set": {
                "status": JobStatus.FAILED,
                "error_log": final_error_log
            }}
        )
        _schedule(_broadcast_status(job_id, JobStatus.FAILED))
