"""
GOPHORA Production Backend - High Quality Job Scraping System
Features:
- Separate collections for skill-based and temp jobs
- Source URLs stored for apply redirects
- Automated 24/7 scraping
- User skill matching
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
import logging

from backend.firebase_config import FirestoreHelper, FirestoreCollections, initialize_firebase
from backend.job_storage import JobStorageManager
from backend.automated_scheduler import AutomatedJobScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
job_manager = None
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global job_manager, scheduler
    logger.info("🚀 Starting GOPHORA Production Backend...")
    
    initialize_firebase()
    job_manager = JobStorageManager()
    scheduler = AutomatedJobScheduler()
    
    # Start automated scraping
    scheduler.start()
    
    logger.info("✅ GOPHORA Backend ready with automated job scraping!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if scheduler:
        scheduler.stop()

app = FastAPI(
    title="GOPHORA Job Platform API",
    description="High-quality job scraping with skill matching",
    version="2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserSkills(BaseModel):
    skills: List[str]

class JobApplication(BaseModel):
    job_id: str
    user_id: Optional[str] = None

# Health check
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "GOPHORA Job Platform API",
        "version": "2.0",
        "features": [
            "Skill-based job matching",
            "Temp/low-skill jobs",
            "Source URL redirects",
            "24/7 automated scraping"
        ]
    }

@app.get("/health")
def health():
    scheduler_status = scheduler.get_status() if scheduler else {"status": "not initialized"}
    return {
        "status": "healthy",
        "scheduler": scheduler_status
    }

# Job endpoints
@app.get("/api/jobs/skill-based")
async def get_skill_based_jobs(limit: int = 20):
    """
    Get skill-based jobs (for users with specific skills)
    These jobs have source URLs for apply redirects
    """
    try:
        firestore = FirestoreHelper()
        jobs = firestore.get_all_documents(
            FirestoreCollections.SKILL_BASED_JOBS,
            filters=[('status', '==', 'active')],
            limit=limit
        )
        
        # Ensure each job has a source_url for apply redirect
        for job in jobs:
            if not job.get('source_url') and job.get('url'):
                job['source_url'] = job['url']
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching skill-based jobs: {e}")
        return []

@app.post("/api/jobs/skill-matched")
async def get_skill_matched_jobs(user_skills: UserSkills, limit: int = 20):
    """
    Get jobs matching user's skills
    Returns jobs with source URLs for redirects
    """
    try:
        jobs = job_manager.get_jobs_for_user_skills(user_skills.skills, limit)
        
        # Ensure source URLs
        for job in jobs:
            if not job.get('source_url') and job.get('url'):
                job['source_url'] = job['url']
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching skill-matched jobs: {e}")
        return []

@app.get("/api/jobs/temp")
async def get_temp_jobs(limit: int = 20):
    """
    Get low-skill/temporary jobs (immediate start)
    These jobs have source URLs for apply redirects
    """
    try:
        jobs = job_manager.get_temp_jobs(limit)
        
        # Ensure source URLs
        for job in jobs:
            if not job.get('source_url') and job.get('url'):
                job['source_url'] = job['url']
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching temp jobs: {e}")
        return []

@app.get("/api/jobs/immediate")
async def get_immediate_jobs(limit: int = 50):
    """
    Get all immediate/entry-level jobs (temp + entry skill-based)
    Returns jobs with source URLs for apply button redirects
    """
    try:
        jobs = job_manager.get_all_immediate_jobs(limit)
        
        # Ensure all jobs have source_url for apply redirects
        for job in jobs:
            if not job.get('source_url'):
                if job.get('url'):
                    job['source_url'] = job['url']
                else:
                    logger.warning(f"Job missing URL: {job.get('title')}")
        
        return jobs
    except Exception as e:
        logger.error(f"Error fetching immediate jobs: {e}")
        return []

@app.get("/api/opportunities/recommend")
async def get_recommendations(limit: int = 20):
    """
    Legacy endpoint - returns immediate jobs for compatibility
    All jobs include source_url for apply button redirects
    """
    try:
        jobs = job_manager.get_all_immediate_jobs(limit)
        
        # Ensure source URLs for apply redirects
        for job in jobs:
            if not job.get('source_url'):
                job['source_url'] = job.get('url', '')
        
        return jobs
    except Exception as e:
        logger.error(f"Error in recommendations: {e}")
        return []

# Manual scraping triggers (for admin/testing)
@app.post("/api/admin/scrape/skill-jobs")
async def trigger_skill_scrape(skills: Optional[List[str]] = None):
    """Manually trigger skill-based job scraping"""
    try:
        stats = job_manager.scrape_and_store_skill_jobs(skills)
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/scrape/temp-jobs")
async def trigger_temp_scrape():
    """Manually trigger temp job scraping"""
    try:
        stats = job_manager.scrape_and_store_temp_jobs()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/scrape/all")
async def trigger_full_scrape(skills: Optional[List[str]] = None):
    """Manually trigger full job scraping"""
    try:
        stats = job_manager.scrape_and_store_all(skills)
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    if scheduler:
        return scheduler.get_status()
    return {"status": "not initialized"}

# Application tracking
@app.post("/api/applications/track")
async def track_application(application: JobApplication):
    """
    Track when user clicks apply (for analytics)
    Actual application happens on external site
    """
    try:
        firestore = FirestoreHelper()
        
        # Log application click
        app_data = {
            "job_id": application.job_id,
            "user_id": application.user_id,
            "clicked_at": str(__import__('datetime').datetime.utcnow()),
            "status": "redirected_to_source"
        }
        
        firestore.add_document(FirestoreCollections.APPLICATIONS, app_data)
        
        # Increment application count on job
        job_collection = None
        
        # Try skill-based jobs first
        job = firestore.get_document(FirestoreCollections.SKILL_BASED_JOBS, application.job_id)
        if job:
            job_collection = FirestoreCollections.SKILL_BASED_JOBS
        else:
            # Try immediate jobs
            job = firestore.get_document(FirestoreCollections.IMMEDIATE_JOBS, application.job_id)
            if job:
                job_collection = FirestoreCollections.IMMEDIATE_JOBS
        
        if job and job_collection:
            current_apps = job.get('applications', 0)
            firestore.update_document(
                job_collection,
                application.job_id,
                {'applications': current_apps + 1}
            )
        
        return {"success": True, "message": "Application tracked"}
    except Exception as e:
        logger.error(f"Error tracking application: {e}")
        return {"success": False, "error": str(e)}

# Legacy endpoints for compatibility
@app.get("/api/opportunities/me")
async def get_my_opportunities():
    return []

@app.get("/api/opportunities/{opportunity_id}/applications")
async def get_applications(opportunity_id: str):
    return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
