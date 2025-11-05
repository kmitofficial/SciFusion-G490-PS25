from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.api.v1 import router as api_router_v1
from server.core.lifespan import lifespan

app = FastAPI(
    title="SciFusion API - Stage 4",
    description="API with split routers and a stub user.",
    lifespan=lifespan
)

# --- ✅ Enable CORS ---
origins = [
    "http://localhost:3000",      # React frontend local dev
    "http://127.0.0.1:3000",
    "https://your-frontend-domain.com",  # Deployed frontend (if any)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],            # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],            # Allows all headers
)

# --- Root route ---
@app.get("/", tags=["Root"])
def get_root():
    return {"message": "SciFusion API is running. See /docs for endpoints."}

# --- Include all API routes ---
app.include_router(api_router_v1, prefix="/api/v1")
