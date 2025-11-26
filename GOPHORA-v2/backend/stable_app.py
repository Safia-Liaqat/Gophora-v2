"""Stable GOPHORA Backend - using lifespan events"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
firestore = None
recommendation_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global firestore, recommendation_engine
    logger.info("🚀 Starting GOPHORA...")
    
    from backend.firebase_config import initialize_firebase, FirestoreHelper
    from backend.recommendation_engine import JobRecommendationEngine
    
    initialize_firebase()
    firestore = FirestoreHelper()
    recommendation_engine = JobRecommendationEngine()
    
    logger.info("✅ GOPHORA ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(title="GOPHORA Backend", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "GOPHORA Backend"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Auth endpoints
@app.post("/api/auth/register")
async def register(data: dict):
    try:
        from backend.auth import register_user
        result = register_user(data)
        return result
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(data: dict):
    try:
        from backend.auth import login_user
        result = login_user(data)
        return result
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail=str(e))

# Job endpoints
@app.get("/api/jobs/immediate")
async def get_immediate_jobs():
    try:
        jobs = recommendation_engine.get_immediate_jobs(20)
        return jobs or []
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        return []

@app.get("/api/opportunities/recommend")
async def get_recommendations():
    try:
        jobs = recommendation_engine.get_immediate_jobs(20)
        return jobs or []
    except:
        return []

@app.get("/api/opportunities/me")
async def get_my_opportunities():
    return []

@app.get("/api/opportunities/{opportunity_id}/applications")
async def get_applications(opportunity_id: str):
    return []

@app.post("/api/applications/apply")
async def apply(opportunity_id: str):
    from backend.firebase_config import FirestoreCollections
    try:
        application = {
            "opportunity_id": opportunity_id,
            "status": "pending",
            "applied_at": str(datetime.utcnow())
        }
        firestore.add_document(FirestoreCollections.APPLICATIONS, application)
        return {"success": True, "message": "Application submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
