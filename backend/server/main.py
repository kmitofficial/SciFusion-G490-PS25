from fastapi import FastAPI
from server.api.v1 import router as api_router_v1
from server.core.lifespan import lifespan

app = FastAPI(
    title="SciFusion API - Stage 4",
    description="API with split routers and a stub user.",
    lifespan=lifespan
)


@app.get("/", tags=["Root"])
def get_root():
    return {"message": "SciFusion API is running. See /docs for endpoints."}


# This line includes everything from api/v1.py,
# which now includes everything from our new router files.
app.include_router(api_router_v1, prefix="/api/v1")
