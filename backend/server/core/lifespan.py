import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from server.core.db import db
from server.services.websocket import manager
from server.models.job import Job
from pydantic_mongo import PydanticObjectId


async def watch_jobs_collection():
    """
    This is the "database watcher."
    It listens for any 'update' operations on the 'jobs' collection.
    """
    print("Starting MongoDB Change Stream listener...")
    jobs_collection = db.get_jobs_collection_async()

    try:
        # Create a change stream pipeline
        pipeline = [{
            '$match': {
                'operationType': 'update'
            }
        }]

        async with jobs_collection.watch(pipeline) as stream:
            async for change in stream:
                try:
                    doc_id = change["documentKey"]["_id"]

                    # When a change happens, get the FULL updated job
                    updated_job_doc = await jobs_collection.find_one({"_id": doc_id})

                    if not updated_job_doc:
                        continue

                    # Convert to our Pydantic model
                    job = Job(**updated_job_doc)
                    user_id = str(job.user_id)  # Find out *who* this job belongs to

                    # Create the message to send
                    message = {
                        "type": "JOB_UPDATE",
                        "data": job.model_dump(mode="json")  # Send the full job object
                    }

                    # Use the manager to send the update to the correct user
                    await manager.send_json(user_id, message)

                except Exception as e:
                    print(f"Error processing change stream event: {e}")

    except Exception as e:
        print(f"Change stream disconnected: {e}. Retrying in 5s...")
        await asyncio.sleep(5)
        asyncio.create_task(watch_jobs_collection())  # Relaunch listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager. This runs on app startup.
    """
    # Start our database watcher in the background
    asyncio.create_task(watch_jobs_collection())
    yield
    # (Code here would run on shutdown)