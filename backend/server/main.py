import json
from typing import Optional, Set

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api.v1 import router as api_router_v1
from server.core.config import settings
from server.core.lifespan import lifespan

app = FastAPI(
    title="SciFusion API - Stage 4",
    description="API with split routers and a stub user.",
    lifespan=lifespan
)

# --- ✅ Enable CORS ---
def _parse_extra_origins(raw_origins: Optional[str]) -> Set[str]:
    if not raw_origins:
        return set()

    try:
        parsed = json.loads(raw_origins)
        if isinstance(parsed, list):
            return {str(origin).strip() for origin in parsed if str(origin).strip()}
    except json.JSONDecodeError:
        pass

    return {origin.strip() for origin in raw_origins.split(",") if origin.strip()}


default_origins = {
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "https://0.0.0.0:3000",
    "http://[::1]:3000",
    "https://[::1]:3000",
}

extra_origins = _parse_extra_origins(settings.CORS_ALLOWED_ORIGINS)
allowed_origins = sorted(default_origins.union(extra_origins))

cors_regex = settings.CORS_ALLOW_ORIGIN_REGEX or None

print("[CORS] allow_origins=", allowed_origins)
if cors_regex:
    print("[CORS] allow_origin_regex=", cors_regex)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=cors_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Root route ---
@app.get("/", tags=["Root"])
def get_root():
    return {"message": "SciFusion API is running. See /docs for endpoints."}

# --- Include all API routes ---
app.include_router(api_router_v1, prefix="/api/v1")
