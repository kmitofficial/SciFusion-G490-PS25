import subprocess
import sys
import os
import asyncio
import json
from pathlib import Path
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

# Get BOTH collections
jobs_collection_sync = db.get_jobs_collection_sync()
jobs_collection_async = db.get_jobs_collection_async()


# --- NEW: Helper to broadcast status ---
async def _broadcast_status(job_id: str, status: str, extra: Dict[str, Any] = None):
    payload = {"type": "JOB_STATUS_UPDATE", "data": {"status": status, **(extra or {})}}
    await manager.broadcast(payload, job_id)


async def _push_log(job_id: str, message: str, log_type: str = "info"):
    """Push log message to frontend"""
    payload = {"type": "AIDER_LOG", "data": {"message": message, "log_type": log_type}}
    await manager.broadcast(payload, job_id)


# --- NEW: Direct pipeline invocation (NO subprocess) ---
async def generate_code_for_idea(job_id: str):
    """
    Called when user approves an idea. This triggers the experiment execution.
    Runs the pipeline directly without subprocess.
    """
    job = await jobs_collection_async.find_one({"_id": ObjectId(job_id)})
    if not job:
        print(f"[RESEARCH SERVICE] Job {job_id} not found")
        return

    # Update status to running
    await jobs_collection_async.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"status": JobStatus.RUNNING}}
    )
    await _broadcast_status(job_id, JobStatus.RUNNING)
    await _push_log(job_id, "Starting experiments after human approval...", "info")

    # Run experiments in background thread (to not block async loop)
    import threading
    thread = threading.Thread(target=_run_experiments_sync, args=(job_id, job))
    thread.daemon = True
    thread.start()


def _run_experiments_sync(job_id: str, job: dict):
    """
    Synchronous function that runs the experiment pipeline.
    This is called in a separate thread.
    """
    try:
        # Import the actual pipeline functions
        import os.path as osp
        from dolphin_utils.experiments_utils import perform_experiments
        from pathlib import Path
        
        print(f"[RESEARCH SERVICE] Running experiments for job {job_id}")
        
        # Get job parameters
        req = job.get("request", {})
        experiment = req.get("experiment", "sentiment_classification_sst2")
        code_model = req.get("code_model", "flash")
        
        # Setup paths
        backend_dir = Path(__file__).parent.parent.parent
        base_dir = backend_dir / "examples" / experiment
        results_dir = backend_dir / "results" / f"api_job_{job_id}"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load ideas from the saved file
        ideas_file = base_dir / f"ideas_round_{req.get('round', 0)}_with_pos.json"
        if not ideas_file.exists():
            ideas_file = base_dir / "ideas.json"
        
        if not ideas_file.exists():
            print(f"[RESEARCH SERVICE] Ideas file not found: {ideas_file}")
            _update_job_status_sync(job_id, "failed")
            return
        
        with open(ideas_file, "r") as f:
            ideas = json.load(f)
        
        novel_ideas = [idea for idea in ideas if idea.get("novel", False) and idea.get("independence", True)]
        
        if not novel_ideas:
            novel_ideas = ideas  # Use all if none are marked as novel
        
        print(f"[RESEARCH SERVICE] Loaded {len(novel_ideas)} ideas to run")
        
        # For now, just call launch_dolphin with resume flags
        # This is simpler and keeps all the Aider/experiment logic in one place
        python_executable = sys.executable
        script_path = str(backend_dir / "launch_dolphin.py")
        
        command = [
            python_executable, script_path,
            "--model", req.get("model", "gemini-2.5-flash-lite"),
            "--code_model", code_model,
            "--experiment", experiment,
            "--topic", req.get("topic", ""),
            "--num-ideas", str(req.get("num_ideas", 3)),
            "--round", str(req.get("round", 0)),
            "--save_name", f"api_job_{job_id}",
            "--job-id", job_id,
            "--skip-idea-generation",  # Skip idea generation
            "--skip-novelty-check",     # Skip novelty check
        ]
        
        if req.get("rag"):
            command.append("--rag")
        if req.get("check_similarity"):
            command.append("--check_similarity")
        
        print(f"[RESEARCH SERVICE] Running command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(backend_dir)
            )
            
            print(f"[RESEARCH SERVICE] Process exit code: {result.returncode}")
            if result.stdout:
                print(f"[RESEARCH SERVICE] stdout: {result.stdout[-500:]}")  # Last 500 chars
            if result.stderr:
                print(f"[RESEARCH SERVICE] stderr: {result.stderr[-500:]}")
            
            if result.returncode == 0:
                _update_job_status_sync(job_id, "complete")
                print(f"[RESEARCH SERVICE] Experiments completed successfully")
            else:
                _update_job_status_sync(job_id, "failed")
                print(f"[RESEARCH SERVICE] Experiments failed")
                
        except Exception as e:
            print(f"[RESEARCH SERVICE] Error running subprocess: {e}")
            _update_job_status_sync(job_id, "failed")
        
        # Update status to completed
        _update_job_status_sync(job_id, "complete")
        print(f"[RESEARCH SERVICE] All experiments completed for job {job_id}")
        
    except Exception as e:
        print(f"[RESEARCH SERVICE] Fatal error running experiments: {e}")
        import traceback
        traceback.print_exc()
        _update_job_status_sync(job_id, "failed")


def _update_job_status_sync(job_id: str, status: str):
    """Update job status synchronously"""
    try:
        jobs_collection_sync.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": status}}
        )
        print(f"[RESEARCH SERVICE] Updated job {job_id} status to {status}")
    except Exception as e:
        print(f"[RESEARCH SERVICE] Error updating status: {e}")


async def run_experiment(job_id: str):
    job = await jobs_collection_async.find_one({"_id": ObjectId(job_id)})
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

    await jobs_collection_async.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "status": job["status"],
            "experiment_results": job["experiment_results"],
            "current_idea_idx": job["current_idea_idx"]
        }}
    )
    await _broadcast_status(job_id, job["status"])


async def generate_next_idea_with_feedback(job_id: str):
    job = await jobs_collection_async.find_one({"_id": ObjectId(job_id)})
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

    await jobs_collection_async.update_one(
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
            jobs_collection_sync.update_one({"_id": job_oid}, {"$set": job_update})

            # --- Pause for human if enabled ---
            if req.rag:  # using rag as proxy for HITL
                jobs_collection_sync.update_one(
                    {"_id": job_oid},
                    {"$set": {"status": JobStatus.PENDING_HUMAN_IDEA}}
                )
                _schedule(_broadcast_status(job_id, JobStatus.PENDING_HUMAN_IDEA))
            else:
                # Auto-proceed
                _schedule(generate_code_for_idea(job_id))

        else:
            print(f"--- [Job: {job_id}] Script Failed (Return Code {process.returncode}) ---")
            jobs_collection_sync.update_one(
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
        jobs_collection_sync.update_one(
            {"_id": job_oid},
            {"$set": {
                "status": JobStatus.FAILED,
                "error_log": final_error_log
            }}
        )
        _schedule(_broadcast_status(job_id, JobStatus.FAILED))
