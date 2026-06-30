import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.router import api_router
from app.services.network_simulator import simulator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create SQL database tables if they do not exist
    Base.metadata.create_all(bind=engine)
    
    # 2. Seed initial device state values
    db = SessionLocal()
    try:
        simulator.seed_database(db)
    finally:
        db.close()
        
    # 3. Trigger simulation loop running in the background
    sim_task = asyncio.create_task(simulator.broadcast_loop())
    
    yield
    
    # 4. Cleanup on shutdown
    sim_task.cancel()
    try:
        await sim_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.0.0"
)

# Configure CORS for local development access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In air-gapped system, wildcard allows any local interface connection
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router under settings prefix (/api)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount router directly under root to handle user-specified endpoints (e.g. GET /devices directly)
app.include_router(api_router)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": "air-gapped"
    }
