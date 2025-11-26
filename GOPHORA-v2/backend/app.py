"""
GOPHORA FastAPI Backend - Main Application
AI-powered job scraping, validation, and personalized recommendations
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend modules
from backend import models
from backend.firebase_config import FirestoreHelper, FirestoreCollections, initialize_firebase
from backend.recommendation_engine import JobRecommendationEngine
from backend import auth

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="GOPHORA AI Backend",
    version="2.0.0",
    description="AI-powered job scraping, validation, and personalized recommendations"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services globally
firestore = None
recommendation_engine = None
scheduler_instance = None


# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup"""
    global firestore, recommendation_engine, scheduler_instance
    
    try:
        logger.info("🚀 Starting GOPHORA AI Backend...")
        
        # Initialize Firebase
        logger.info("📦 Initializing Firebase...")
        initialize_firebase()
        firestore = FirestoreHelper()
        logger.info("✅ Firebase connected successfully!")
        
        # Initialize recommendation engine
        logger.info("🤖 Initializing AI recommendation engine...")
        recommendation_engine = JobRecommendationEngine()
        logger.info("✅ Recommendation engine ready!")
        
        # Initialize and start scheduler - DISABLED
        logger.info("ℹ️  Background scheduler disabled for stability")
        scheduler_instance = None
        
        logger.info("🎉 GOPHORA backend started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        logger.error("   The backend will run with limited functionality.")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services on shutdown"""
    global scheduler_instance
    try:
        if scheduler_instance:
            scheduler_instance.stop()
            logger.info("⏹️  Background scraping scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


# ==================== HEALTH & INFO ====================

@app.get("/")
async def root():
    """Root endpoint - Health check"""
    return {
        "status": "ok",
        "service": "GOPHORA AI Backend",
        "version": "2.0.0",
        "message": "Welcome to GOPHORA! Visit /docs for API documentation."
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    global scheduler_instance
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "firebase": "connected" if firestore else "disconnected",
            "recommendation_engine": "ready" if recommendation_engine else "not initialized",
            "scraper": "running" if (scheduler_instance and scheduler_instance.scheduler.running) else "stopped"
        }
    }


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
            "message": "User registered successfully",
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
async def login_user(credentials: models.UserLogin):
    """Login user"""
    try:
        # Get user by email
        users = firestore.query_documents(
            FirestoreCollections.USERS,
            [("email", "==", credentials.email)]
        )
        
        if not users:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = users[0]
        
        # Verify password
        if not auth.verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate token
        token = auth.create_access_token(
            data={"sub": user["email"], "role": user["role"]}
        )
        
        return {
            "success": True,
            "message": "Login successful",
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
        raise HTTPException(status_code=500, detail="Login failed")


# ==================== JOBS - IMMEDIATE (ZERO-EFFORT) ====================

@app.get("/api/jobs/immediate")
async def get_immediate_jobs(limit: int = 20):
    """
    Get immediate, zero/low-skill jobs available to ALL users
    These jobs require no skills and offer immediate start + quick payment
    """
    try:
        jobs = recommendation_engine.get_immediate_jobs(limit=limit)
        return {
            "success": True,
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
        return {
            "success": True,
            **recommendations
        }
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/skill-based/{user_id}")
async def get_skill_based_jobs(user_id: str, limit: int = 30):
    """Get skill-based jobs matched to user's profile"""
    try:
        jobs = recommendation_engine.get_skill_based_jobs(user_id, limit=limit)
        return {
            "success": True,
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
            "success": True,
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
            "success": True,
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
            "success": True,
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
            "success": True,
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
        
        return {
            "success": True,
            "profile": profiles[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/users/{user_id}/profile")
async def update_user_profile(user_id: str, profile_data: dict):
    """Update user profile with flexible fields"""
    try:
        profiles = firestore.query_documents(
            FirestoreCollections.PROFILES,
            [("user_id", "==", user_id)]
        )
        
        if not profiles:
            # Create profile if it doesn't exist
            profile_dict = {
                "user_id": user_id,
                "avatar_url": profile_data.get("avatar_url"),
                "bio": profile_data.get("bio"),
                "skills": profile_data.get("skills", []),
                "interests": profile_data.get("interests", []),
                "company_name": profile_data.get("company_name"),
                "company_website": profile_data.get("company_website"),
                "country": profile_data.get("country"),
                "city": profile_data.get("city"),
                "trust_score": 0,
                "verification_status": "unverified",
                "updated_at": datetime.utcnow().isoformat()
            }
            firestore.add_document(FirestoreCollections.PROFILES, profile_dict)
        else:
            profile_id = profiles[0]["id"]
            update_data = {k: v for k, v in profile_data.items() if v is not None}
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            firestore.update_document(
                FirestoreCollections.PROFILES,
                profile_id,
                update_data
            )
        
        return {
            "success": True,
            "message": "Profile updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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
        
        return {
            "success": True,
            "message": "Application submitted successfully",
            "application": {"id": app_id, **app_dict}
        }
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
        
        return {
            "success": True,
            "applications": applications,
            "count": len(applications)
        }
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ADMIN - SCRAPING CONTROL ====================

@app.get("/api/admin/scraping-status")
async def get_scraping_status():
    """Get current scraping scheduler status"""
    global scheduler_instance
    
    try:
        if not scheduler_instance:
            return {
                "success": False,
                "message": "Scheduler not initialized",
                "running": False
            }
        
        status = scheduler_instance.get_scheduler_status()
        return {
            "success": True,
            **status
        }
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/trigger-scrape")
async def trigger_manual_scrape(background_tasks: BackgroundTasks):
    """Manually trigger a scraping job"""
    global scheduler_instance
    
    try:
        if not scheduler_instance:
            # Import scheduler dynamically if not initialized
            from backend.scheduler import scraping_scheduler
            scheduler_instance = scraping_scheduler
        
        background_tasks.add_task(scheduler_instance.scrape_and_validate_jobs)
        
        return {
            "success": True,
            "message": "Scraping job triggered successfully. Check /api/admin/scraping-logs for results."
        }
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
        
        return {
            "success": True,
            "logs": logs,
            "count": len(logs)
        }
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
        
        scraper_status = "unknown"
        if scheduler_instance:
            scraper_status = "running" if scheduler_instance.scheduler.running else "stopped"
        
        return {
            "success": True,
            "statistics": {
                "total_scraped": len(scraped_jobs),
                "total_verified": len(verified_jobs),
                "immediate_jobs": len(immediate_jobs),
                "skill_based_jobs": len(skill_jobs),
                "total_users": len(users),
                "total_applications": len(applications)
            },
            "scraper_status": scraper_status
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ADDITIONAL ENDPOINTS FOR FRONTEND ====================

@app.get("/api/opportunities/recommend")
async def get_recommendations():
    """Get recommended opportunities for seeker"""
    try:
        jobs = recommendation_engine.get_immediate_jobs(limit=20)
        return jobs if jobs else []
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []

@app.get("/api/opportunities/me")
async def get_my_opportunities():
    """Get provider's opportunities"""
    try:
        return []
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        return []

@app.get("/api/opportunities/{opportunity_id}/applications")
async def get_opportunity_applications(opportunity_id: str):
    """Get applications for an opportunity"""
    try:
        apps = firestore.query_documents(
            FirestoreCollections.APPLICATIONS,
            [("opportunity_id", "==", opportunity_id)]
        )
        return apps if apps else []
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        return []

@app.post("/api/applications/apply")
async def apply_to_opportunity(opportunity_id: str):
    """Apply to an opportunity"""
    try:
        app_dict = {
            "opportunity_id": opportunity_id,
            "user_id": "temp_user",
            "status": "pending",
            "applied_at": datetime.utcnow().isoformat()
        }
        app_id = firestore.add_document(FirestoreCollections.APPLICATIONS, app_dict)
        return {"success": True, "application_id": app_id}
    except Exception as e:
        logger.error(f"Error applying: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/verification/status")
async def get_verification_status():
    """Get verification status"""
    return {
        "status": "not_verified",
        "trust_score": 0,
        "reason": "Verification not yet completed"
    }


# ==================== TEST ENDPOINT ====================

@app.get("/test-firebase")
async def test_firebase():
    """Test Firebase read/write operations"""
    try:
        # Test write
        test_data = {
            "message": "Test from GOPHORA AI Backend",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        doc_id = firestore.add_document("test_collection", test_data)
        
        # Test read
        doc = firestore.get_document("test_collection", doc_id)
        
        return {
            "success": True,
            "message": "Firebase read/write successful",
            "test_data": doc
        }
    except Exception as e:
        logger.error(f"Firebase test error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
