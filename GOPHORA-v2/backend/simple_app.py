"""
Minimal GOPHORA Backend - No scheduler, just core features
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(title="GOPHORA Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
firestore = None
recommendation_engine = None
scheduler = None

@app.on_event("startup")
async def startup():
    global firestore, recommendation_engine, scheduler
    logger.info("🚀 Starting GOPHORA...")
    
    from backend.firebase_config import initialize_firebase, FirestoreHelper
    from backend.recommendation_engine import JobRecommendationEngine
    # from backend.scheduler import ScrapingScheduler  # DISABLED - causes crashes
    
    initialize_firebase()
    firestore = FirestoreHelper()
    recommendation_engine = JobRecommendationEngine()
    
    # DISABLED SCHEDULER - uncomment to enable scraping
    # scheduler = ScrapingScheduler()
    # scheduler.start()
    # logger.info("✅ Scheduler started - scraping 24/7")
    
    logger.info("✅ GOPHORA ready! (Scheduler disabled)")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down...")
    # global scheduler
    # if scheduler:
    #     scheduler.stop()
    #     logger.info("Scheduler stopped")

@app.get("/")
def root():
    return {"status": "ok", "message": "GOPHORA Backend"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/auth/register")
async def register(user_data: dict):
    from backend import auth, models
    from backend.firebase_config import FirestoreCollections
    
    try:
        # Check existing
        existing = firestore.query_documents(
            FirestoreCollections.USERS,
            "email",
            "==",
            user_data["email"]
        )
        if existing:
            raise HTTPException(400, "Email already registered")
        
        # Create user
        password_hash = auth.get_password_hash(user_data["password"])
        user_dict = {
            "email": user_data["email"],
            "password_hash": password_hash,
            "full_name": user_data.get("full_name", ""),
            "role": user_data.get("role", "seeker"),
            "created_at": datetime.utcnow().isoformat()
        }
        
        user_id = firestore.add_document(FirestoreCollections.USERS, user_dict)
        
        # Create profile
        profile_dict = {
            "user_id": user_id,
            "skills": [],
            "interests": [],
            "country": None,
            "city": None
        }
        firestore.add_document(FirestoreCollections.PROFILES, profile_dict)
        
        # Generate token
        token = auth.create_access_token({"sub": user_dict["email"], "role": user_dict["role"]})
        
        return {
            "success": True,
            "user": {**user_dict, "id": user_id},
            "access_token": token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(500, str(e))

@app.post("/api/auth/login")
async def login(credentials: dict):
    from backend import auth
    from backend.firebase_config import FirestoreCollections
    
    try:
        users = firestore.query_documents(
            FirestoreCollections.USERS,
            "email",
            "==",
            credentials["email"]
        )
        
        if not users:
            raise HTTPException(401, "Invalid email or password")
        
        user = users[0]
        
        if not auth.verify_password(credentials["password"], user["password_hash"]):
            raise HTTPException(401, "Invalid email or password")
        
        token = auth.create_access_token({"sub": user["email"], "role": user["role"]})
        
        return {
            "success": True,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"]
            },
            "access_token": token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(500, "Login failed")

@app.put("/api/users/{user_id}/profile")
async def update_profile(user_id: str, profile_data: dict):
    from backend.firebase_config import FirestoreCollections
    
    try:
        profiles = firestore.query_documents(
            FirestoreCollections.PROFILES,
            "user_id",
            "==",
            user_id
        )
        
        if not profiles:
            profile_dict = {
                "user_id": user_id,
                **profile_data,
                "updated_at": datetime.utcnow().isoformat()
            }
            firestore.add_document(FirestoreCollections.PROFILES, profile_dict)
        else:
            profile_id = profiles[0]["id"]
            firestore.update_document(
                FirestoreCollections.PROFILES,
                profile_id,
                {**profile_data, "updated_at": datetime.utcnow().isoformat()}
            )
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/jobs/immediate")
async def get_immediate_jobs():
    try:
        jobs = recommendation_engine.get_immediate_jobs(20)
        return {"success": True, "jobs": jobs or [], "count": len(jobs) if jobs else 0}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"success": True, "jobs": [], "count": 0}

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
        app_dict = {
            "opportunity_id": opportunity_id,
            "user_id": "temp",
            "status": "pending",
            "applied_at": datetime.utcnow().isoformat()
        }
        app_id = firestore.add_document(FirestoreCollections.APPLICATIONS, app_dict)
        return {"success": True, "application_id": app_id}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/verification/status")
async def verification_status():
    return {"status": "not_verified", "trust_score": 0, "reason": ""}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
