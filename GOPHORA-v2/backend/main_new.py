"""
GOPHORA FastAPI Backend - Firebase Version
Main application with AI-powered job scraping and validation
"""
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime
import logging

from . import models
from .firebase_config import FirestoreHelper, FirestoreCollections
from .scheduler import scraping_scheduler
from .recommendation_engine import JobRecommendationEngine
from .ai_validation import AIValidationPipeline
from . import auth

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="GOPHORA AI Backend", version="2.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
firestore = FirestoreHelper()
recommendation_engine = JobRecommendationEngine()
ai_validator = AIValidationPipeline()

# Security
security = HTTPBearer()


# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Start background scraping scheduler on app startup"""
    try:
        logger.info("Starting GOPHORA backend...")
        scraping_scheduler.start()
        logger.info("Background scraping scheduler started successfully")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background scheduler on shutdown"""
    try:
        scraping_scheduler.stop()
        logger.info("Background scraping scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


# ==================== AUTHENTICATION ====================

@app.post("/api/auth/register")
async def register_user(user_data: models.UserCreate):
    """Register a new user"""
    try:
        # Check if user exists
        existing_users = firestore.query_documents(
            FirestoreCollections.USERS,
            "email", "==", user_data.email
        )
        
        if existing_users:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = auth.get_password_hash(user_data.password)
        
        # Create user
        user_dict = {
            "email": user_data.email,
            "password_hash": password_hash,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        user_id = firestore.add_document(FirestoreCollections.USERS, user_dict)
        
        # Create default profile
        profile_dict = {
            "user_id": user_id,
            "avatar_url": None,
            "bio": None,
            "skills": [],
            "interests": [],
            "company_name": None,
            "company_website": None,
            "country": None,
            "city": None,
            "trust_score": 0,
            "verification_status": "unverified"
        }
        
        firestore.add_document(FirestoreCollections.PROFILES, profile_dict)
        
        # Generate token
        token = auth.create_access_token(data={"sub": user_dict["email"], "user_id": user_id})
        
        return {
            "user": {**user_dict, "id": user_id},
            "access_token": token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/api/auth/login")
async def login_user(email: str, password: str):
    """Login user"""
    try:
        # Get user
        users = firestore.query_documents(
            FirestoreCollections.USERS,
            "email", "==", email
        )
        
        if not users:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = users[0]
        
        # Verify password
        if not auth.verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate token
        token = auth.create_access_token(data={"sub": email, "user_id": user["id"]})
        
        return {
            "user": user,
            "access_token": token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


# ==================== JOBS - IMMEDIATE (ZERO-EFFORT) ====================

@app.get("/api/jobs/immediate")
async def get_immediate_jobs(limit: int = 20):
    """
    Get immediate, zero/low-skill jobs available to ALL users
    These are promoted jobs that anyone can start within 24-48 hours
    """
    try:
        jobs = recommendation_engine.get_immediate_jobs(limit=limit)
        return {
            "jobs": jobs,
            "count": len(jobs),
            "message": "These jobs require zero or minimal skills and offer immediate start"
        }
    except Exception as e:
        logger.error(f"Error getting immediate jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== JOBS - PERSONALIZED ====================

@app.get("/api/jobs/recommended/{user_id}")
async def get_recommended_jobs(user_id: str):
    """
    Get personalized job recommendations for a specific user
    Returns both immediate jobs and skill-based matches
    """
    try:
        recommendations = recommendation_engine.get_recommended_jobs_for_user(user_id)
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/skill-based/{user_id}")
async def get_skill_based_jobs(user_id: str, limit: int = 30):
    """Get skill-based jobs matched to user's profile"""
    try:
        jobs = recommendation_engine.get_skill_based_jobs(user_id, limit=limit)
        return {
            "jobs": jobs,
            "count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error getting skill-based jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== JOBS - SEARCH & FILTER ====================

@app.get("/api/jobs/search")
async def search_jobs(q: str, limit: int = 30):
    """Semantic search for jobs using AI embeddings"""
    try:
        jobs = recommendation_engine.search_jobs(q, limit=limit)
        return {
            "query": q,
            "jobs": jobs,
            "count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/category/{category}")
async def get_jobs_by_category(category: str, limit: int = 30):
    """Get jobs filtered by category (Work, Education, Hobbies, Contribution)"""
    try:
        jobs = recommendation_engine.get_jobs_by_category(category, limit=limit)
        return {
            "category": category,
            "jobs": jobs,
            "count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error getting jobs by category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/location/{location}")
async def get_jobs_by_location(location: str, limit: int = 30):
    """Get jobs filtered by location"""
    try:
        jobs = recommendation_engine.get_jobs_by_location(location, limit=limit)
        return {
            "location": location,
            "jobs": jobs,
            "count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error getting jobs by location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/trending")
async def get_trending_jobs(limit: int = 20):
    """Get trending/popular jobs based on recency and trust score"""
    try:
        jobs = recommendation_engine.get_trending_jobs(limit=limit)
        return {
            "jobs": jobs,
            "count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error getting trending jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== USER PROFILE ====================

@app.get("/api/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    """Get user profile"""
    try:
        profiles = firestore.query_documents(
            FirestoreCollections.PROFILES,
            "user_id", "==", user_id
        )
        
        if not profiles:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profiles[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/users/{user_id}/profile")
async def update_user_profile(user_id: str, profile_data: models.ProfileBase):
    """Update user profile"""
    try:
        profiles = firestore.query_documents(
            FirestoreCollections.PROFILES,
            "user_id", "==", user_id
        )
        
        if not profiles:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_id = profiles[0]["id"]
        
        firestore.update_document(
            FirestoreCollections.PROFILES,
            profile_id,
            profile_data.dict(exclude_unset=True)
        )
        
        return {"message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== APPLICATIONS ====================

@app.post("/api/applications")
async def create_application(application: models.ApplicationCreate):
    """Create a new job application"""
    try:
        app_dict = {
            **application.dict(),
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        app_id = firestore.add_document(FirestoreCollections.APPLICATIONS, app_dict)
        
        return {"id": app_id, **app_dict}
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/user/{user_id}")
async def get_user_applications(user_id: str):
    """Get all applications for a user"""
    try:
        applications = firestore.query_documents(
            FirestoreCollections.APPLICATIONS,
            "seeker_id", "==", user_id
        )
        
        return {"applications": applications, "count": len(applications)}
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ADMIN - SCRAPING CONTROL ====================

@app.get("/api/admin/scraping-status")
async def get_scraping_status():
    """Get current scraping scheduler status"""
    try:
        status = scraping_scheduler.get_scheduler_status()
        return status
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/trigger-scrape")
async def trigger_manual_scrape(background_tasks: BackgroundTasks):
    """Manually trigger a scraping job"""
    try:
        background_tasks.add_task(scraping_scheduler.scrape_and_validate_jobs)
        return {"message": "Scraping job triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/scraping-logs")
async def get_scraping_logs(limit: int = 50):
    """Get recent scraping logs"""
    try:
        logs = firestore.get_all_documents(
            FirestoreCollections.SCRAPING_LOGS,
            limit=limit
        )
        
        # Sort by timestamp descending
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        # Count documents in each collection
        scraped_jobs = firestore.get_all_documents(FirestoreCollections.SCRAPED_JOBS)
        verified_jobs = firestore.get_all_documents(FirestoreCollections.VERIFIED_JOBS)
        immediate_jobs = firestore.get_all_documents(FirestoreCollections.IMMEDIATE_JOBS)
        skill_jobs = firestore.get_all_documents(FirestoreCollections.SKILL_BASED_JOBS)
        users = firestore.get_all_documents(FirestoreCollections.USERS)
        applications = firestore.get_all_documents(FirestoreCollections.APPLICATIONS)
        
        return {
            "total_scraped": len(scraped_jobs),
            "total_verified": len(verified_jobs),
            "immediate_jobs": len(immediate_jobs),
            "skill_based_jobs": len(skill_jobs),
            "total_users": len(users),
            "total_applications": len(applications),
            "scraper_status": scraping_scheduler.get_scheduler_status()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HEALTH CHECK ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "GOPHORA AI Backend",
        "version": "2.0",
        "firebase": "connected",
        "scraper": "running" if scraping_scheduler.scheduler.running else "stopped"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "ok",
            "firebase": "ok",
            "scraper": "running" if scraping_scheduler.scheduler.running else "stopped",
            "ai_validation": "ok"
        }
    }
