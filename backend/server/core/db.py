from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from server.core.config import settings


class DBClient:
    """A single class to manage both async and sync db clients."""

    client_async: AsyncIOMotorClient
    db_async: any

    client_sync: MongoClient
    db_sync: any

    def __init__(self, mongo_uri: str, db_name: str):
        try:
            self.client_async = AsyncIOMotorClient(mongo_uri)
            self.db_async = self.client_async[db_name]

            self.client_sync = MongoClient(mongo_uri)
            self.db_sync = self.client_sync[db_name]

            print(f"✅ Successfully connected to MongoDB at {mongo_uri}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def get_jobs_collection_async(self):
        return self.db_async.jobs

    def get_jobs_collection_sync(self):
        return self.db_sync.jobs

    # --- ADD THESE TWO NEW METHODS ---
    def get_users_collection_async(self):
        return self.db_async.users

    def get_users_collection_sync(self):
        return self.db_sync.users
    # --- END OF FIX ---


# Create a single instance to be imported by other files
db = DBClient(settings.MONGODB_URI, settings.DATABASE_NAME)