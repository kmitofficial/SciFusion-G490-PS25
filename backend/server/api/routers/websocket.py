from fastapi import (
    APIRouter, WebSocket, WebSocketDisconnect, Depends
)
from server.models.job import ResearchRequest, Job
from server.models.user import User
from server.services.auth import get_current_user
from server.services.websocket import manager
from server.services import research
from server.core.db import db
import json

router = APIRouter()
jobs_collection = db.get_jobs_collection_async()


@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        # We use our dummy auth to identify the user
        current_user: User = Depends(get_current_user)
):
    user_id = str(current_user.id)
    await manager.connect(user_id, websocket)

    try:
        while True:
            # Wait for a message from the client
            data = await websocket.receive_text()
            message = json.loads(data)

            # --- Handle different message types ---

            if message.get("type") == "START_JOB":
                payload = message.get("payload", {})

                try:
                    # 1. Validate the job request
                    req = ResearchRequest(**payload)

                    # 2. Create the job in the DB
                    new_job = Job(
                        request=req,
                        status="pending",
                        user_id=current_user.id
                    )
                    insert_result = await jobs_collection.insert_one(
                        new_job.model_dump(by_alias=True)
                    )
                    job_id = str(insert_result.inserted_id)

                    # 3. Start the background script (just like we did in Stage 4)
                    background_tasks = BackgroundTasks()
                    background_tasks.add_task(research.run_research_task, job_id, req)

                    # Run the background task
                    await background_tasks()

                    # 4. Send confirmation back to the client
                    await manager.send_json(user_id, {
                        "type": "JOB_STARTED",
                        "data": {"job_id": job_id}
                    })

                except Exception as e:
                    print(f"Failed to start job: {e}")
                    await manager.send_json(user_id, {
                        "type": "ERROR",
                        "data": f"Failed to start job: {e}"
                    })

            # You could add other message types here, e.g., "CANCEL_JOB"

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"Error in WebSocket for user {user_id}: {e}")
        manager.disconnect(user_id)