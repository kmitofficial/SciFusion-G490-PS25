import subprocess
import sys
import os
from server.models.job import ResearchRequest
from server.core.db import db  # Import our single DB instance
from bson import ObjectId

# Get the synchronous 'jobs' collection
# We use sync here because this is a background task,
# not a high-concurrency API route.
jobs_collection = db.get_jobs_collection_sync()


def run_research_task(job_id: str, req: ResearchRequest):
    """
    The background task, now with database updates!
    """

    # 1. Get the job's ObjectId
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

    # 2. Update job status to 'running' in DB
    jobs_collection.update_one(
        {"_id": job_oid},
        {"$set": {"status": "running"}}
    )

    # Build the command
    command = [
        python_executable, script_path,
        "--model", req.model,
        "--code_model", req.code_model,
        "--experiment", req.experiment,
        "--topic", req.topic,
        "--num-ideas", str(req.num_ideas),
        "--round", str(req.round),
        "--save_name", f"api_job_{job_id}",  # Give it a unique name
    ]
    if req.rag: command.append("--rag")
    if req.check_similarity: command.append("--check_similarity")
    if req.skip_novelty_check: command.append("--skip-novelty-check")

    print(f"[Job: {job_id}] Running command: {' '.join(command)}")

    final_update = {}
    try:
        # 3. Run the script and wait for it to complete
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=working_dir
        )

        print(f"--- ✅ [Job: {job_id}] Job Finished ---")

        # 4. Prepare final update for the DB
        final_update = {
            "status": "complete",
            "log": process.stdout,
            "error_log": process.stderr
        }

    except Exception as e:
        print(f"--- ❌ [Job: {job_id}] Job Failed Critically ---")
        final_update = {
            "status": "failed",
            "error_log": str(e)
        }

    # 5. Save final update to MongoDB
    jobs_collection.update_one(
        {"_id": job_oid},
        {"$set": final_update}
    )

    print(f"--- 💾 [Job: {job_id}] Results saved to database. ---")