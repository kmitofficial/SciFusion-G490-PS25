import subprocess
import sys
import os
from server.models.job import ResearchRequest
from server.core.db import db
from bson import ObjectId

# Import the API callback functions from launch_dolphin
# We will call them directly if the script crashes
# We need to add all of them, just in case
try:
    from launch_dolphin import update_job_status
except ImportError:
    # This is a fallback in case of circular imports, though unlikely
    def update_job_status(job_id, status):
        print(f"[RESEARCH_SERVICE] Fallback: Job {job_id} status to {status}")

# Get the synchronous 'jobs' collection
jobs_collection = db.get_jobs_collection_sync()


def run_research_task(job_id: str, req: ResearchRequest):
    """
    The background task, now with
    1. Corrected argparse flags
    2. Final log saving
    """

    try:
        job_oid = ObjectId(job_id)
    except Exception:
        print(f"[Job: {job_id}] ERROR: Invalid Job ID format. Aborting.")
        return

    # --- Setup paths (same as Stage 2) ---
    python_executable = sys.executable
    script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "launch_dolphin.py")
    )
    working_dir = os.path.dirname(script_path)

    print(f"--- 🚀 [Job: {job_id}] Starting Job ---")

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
        "--job-id", job_id  # <-- Pass the job_id
    ]

    # --- THIS IS THE FIX ---
    # Add boolean flags only if they are True
    # Must use hyphens to match argparse in launch_dolphin.py
    if req.rag:
        command.append("--rag")
    if req.check_similarity:
        command.append("--check_similarity")
    if req.skip_novelty_check:
        command.append("--skip-novelty-check")
    # --- END OF FIX ---

    print(f"[Job: {job_id}] Running command: {' '.join(command)}")

    final_log = ""
    final_error_log = ""

    try:
        # Run the script and wait for it to complete
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
            print(f"--- ✅ [Job: {job_id}] Job Finished ---")
            # The script *should* send its own 'complete' status,
            # but we'll save the logs just in case
            jobs_collection.update_one(
                {"_id": job_oid},
                {"$set": {"log": final_log, "error_log": final_error_log}}
            )
        else:
            print(f"--- ❌ [Job: {job_id}] Script Failed (Return Code {process.returncode}) ---")
            # If the script crashed, it didn't send 'complete'
            # Let's save the logs and set status to 'failed'
            jobs_collection.update_one(
                {"_id": job_oid},
                {"$set": {
                    "status": "failed",
                    "log": final_log,
                    "error_log": final_error_log
                }}
            )
            # Manually notify the frontend
            update_job_status(job_id, "failed")

    except Exception as e:
        print(f"--- ❌ [Job: {job_id}] Script Host Failed Critically ---")
        final_error_log = str(e)
        jobs_collection.update_one(
            {"_id": job_oid},
            {"$set": {
                "status": "failed",
                "error_log": final_error_log
            }}
        )
        # Manually notify the frontend
        update_job_status(job_id, "failed")