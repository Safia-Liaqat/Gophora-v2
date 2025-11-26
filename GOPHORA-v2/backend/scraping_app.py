"""
GOPHORA Backend with Job Scraping
Run with: python -m uvicorn backend.scraping_app:app --host 127.0.0.1 --port 8000 --reload
"""
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
firestore = None
recommendation_engine = None
job_storage = None
intelligent_chatbot = None
job_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global firestore, recommendation_engine, job_storage, intelligent_chatbot, job_scheduler
    logger.info("🚀 Starting GOPHORA with AI and automated job scraping...")
    
    try:
        from backend.firebase_config import initialize_firebase, FirestoreHelper
        from backend.recommendation_engine import JobRecommendationEngine
        
        initialize_firebase()
        firestore = FirestoreHelper()
        recommendation_engine = JobRecommendationEngine()
        
        # Initialize job storage
        try:
            from backend.job_storage import JobStorageManager
            job_storage = JobStorageManager()
            logger.info("✅ Job storage initialized!")
        except Exception as e:
            logger.warning(f"Job storage not available: {e}")
            job_storage = None
        
        # Initialize intelligent chatbot with LangChain
        try:
            from backend.intelligent_chatbot import IntelligentChatbot
            intelligent_chatbot = IntelligentChatbot(firestore)
            logger.info("✅ AI Chatbot initialized with LangChain!")
        except Exception as e:
            logger.warning(f"AI Chatbot not available: {e}")
            intelligent_chatbot = None
        
        # Start automated job scraping scheduler (every 15 minutes)
        try:
            from backend.automated_scheduler import AutomatedJobScheduler
            job_scheduler = AutomatedJobScheduler()
            job_scheduler.start()
            logger.info("✅ Automated job scraping started (every 15 minutes)!")
        except Exception as e:
            logger.warning(f"Job scheduler not available: {e}")
            job_scheduler = None
        
        logger.info("✅ GOPHORA ready with AI and automation!")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    if job_scheduler and job_scheduler.is_running:
        job_scheduler.stop()
        logger.info("Job scheduler stopped")
    logger.info("Shutting down...")

app = FastAPI(title="GOPHORA Backend", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
    allow_credentials=True,  # IMPORTANT: Allow cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "GOPHORA Job Platform",
        "version": "2.0"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "job_storage": "available" if job_storage else "not initialized"
    }

# Auth endpoints
@app.post("/api/auth/register")
async def register(data: dict, response: Response):
    """Register new user with 24-hour cookie session"""
    try:
        from backend.firebase_config import FirestoreCollections
        from backend.config import COOKIE_MAX_AGE
        import backend.auth as auth
        
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'seeker')
        name = data.get('name', '')
        
        # Check if user exists
        existing = firestore.query_documents(
            FirestoreCollections.USERS,
            "email", "==", email
        )
        
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Hash password
        password_hash = auth.get_password_hash(password)
        
        # Create user
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        user_id = firestore.add_document(FirestoreCollections.USERS, user_data)
        user_data["id"] = user_id
        
        # Create 24-hour token
        token = auth.create_access_token(
            data={"sub": email, "role": role, "user_id": user_id},
            expires_delta=timedelta(hours=24)
        )
        
        # Set cookie that expires in 24 hours
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=False,
            secure=False,
            samesite="lax",
            max_age=COOKIE_MAX_AGE,
            path="/"
        )
        
        logger.info(f"User registered successfully with 24h cookie: {email}")
        
        return {
            "user": {
                "id": user_id,
                "email": email,
                "role": role,
                "name": name
            },
            "access_token": token,
            "token_type": "bearer",
            "expires_in": COOKIE_MAX_AGE
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(data: dict, response: Response):
    """Login user with 24-hour cookie session"""
    try:
        from backend.firebase_config import FirestoreCollections
        from backend.config import COOKIE_MAX_AGE
        import backend.auth as auth
        
        email = data.get('email')
        password = data.get('password')
        
        logger.info(f"Login attempt for email: {email}")
        
        # Get user
        users = firestore.query_documents(
            FirestoreCollections.USERS,
            "email", "==", email
        )
        
        if not users:
            logger.warning(f"User not found: {email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = users[0]
        logger.info(f"User found: {email}, role: {user.get('role')}")
        
        # Verify password
        if not auth.verify_password(password, user.get("password_hash")):
            logger.warning(f"Invalid password for: {email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create 24-hour token
        token = auth.create_access_token(
            data={
                "sub": email,
                "role": user.get("role"),
                "user_id": user.get("id")
            },
            expires_delta=timedelta(hours=24)
        )
        
        # Set cookie with 24-hour expiry
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=False,
            secure=False,
            samesite="lax",
            max_age=COOKIE_MAX_AGE,
            path="/"
        )
        
        logger.info(f"Login successful with 24h cookie for: {email}")
        
        return {
            "user": {
                "id": user.get("id"),
                "email": user.get("email"),
                "role": user.get("role"),
                "name": user.get("name", "")
            },
            "access_token": token,
            "token_type": "bearer",
            "expires_in": COOKIE_MAX_AGE
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/logout")
async def logout(response: Response):
    """Logout user by clearing the cookie"""
    response.delete_cookie(key="access_token", path="/", samesite="lax")
    logger.info("User logged out - cookie cleared")
    return {"message": "Logged out successfully"}

@app.get("/api/auth/verify")
async def verify_token(request: Request):
    """Verify if user's token is still valid"""
    try:
        from jose import jwt, JWTError
        from backend.config import SECRET_KEY, ALGORITHM
        from backend.firebase_config import FirestoreCollections
        
        # Get token from cookie
        token = request.cookies.get("access_token")
        
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        users = firestore.query_documents(
            FirestoreCollections.USERS,
            "email", "==", email
        )
        
        if not users:
            raise HTTPException(status_code=401, detail="User not found")
        
        user = users[0]
        
        return {
            "valid": True,
            "user": {
                "id": user.get("id"),
                "email": user.get("email"),
                "role": user.get("role"),
                "name": user.get("name", "")
            }
        }
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")

# Job endpoints - with source URLs for apply redirects
@app.get("/api/jobs/immediate")
async def get_immediate_jobs(limit: int = 20):
    """Get immediate jobs with source URLs for apply button"""
    try:
        jobs = recommendation_engine.get_immediate_jobs(limit)
        
        # Ensure all jobs have source_url for apply redirects
        for job in jobs:
            if not job.get('source_url') and job.get('url'):
                job['source_url'] = job['url']
        
        return jobs or []
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        return []

@app.get("/api/opportunities/recommend")
async def get_recommendations(limit: int = 20):
    """Get recommended jobs - all have source URLs for apply button redirects"""
    try:
        jobs = recommendation_engine.get_immediate_jobs(limit)
        
        # Ensure source URLs
        for job in jobs:
            if not job.get('source_url'):
                job['source_url'] = job.get('url', '')
        
        return jobs or []
    except Exception as e:
        logger.error(f"Error: {e}")
        return []

@app.get("/api/jobs/skill-based")
async def get_skill_based_jobs(limit: int = 20):
    """Get skill-based jobs with source URLs"""
    try:
        from backend.firebase_config import FirestoreCollections
        jobs = firestore.get_all_documents(
            FirestoreCollections.SKILL_BASED_JOBS,
            filters=[('status', '==', 'active')],
            limit=limit
        )
        
        # Ensure source URLs
        for job in jobs:
            if not job.get('source_url') and job.get('url'):
                job['source_url'] = job['url']
        
        return jobs
    except Exception as e:
        logger.error(f"Error: {e}")
        return []

@app.get("/api/opportunities")
async def get_all_opportunities(limit: int = 50):
    """Get all opportunities/jobs with source URLs"""
    try:
        # Get immediate jobs
        immediate_jobs = recommendation_engine.get_immediate_jobs(limit // 2)
        
        # Get skill-based jobs
        from backend.firebase_config import FirestoreCollections
        skill_jobs = firestore.get_all_documents(
            FirestoreCollections.SKILL_BASED_JOBS,
            limit=limit // 2
        )
        
        # Combine all jobs
        all_jobs = immediate_jobs + skill_jobs
        
        # Ensure all have source URLs
        for job in all_jobs:
            if not job.get('source_url'):
                job['source_url'] = job.get('url', '')
        
        return all_jobs[:limit]
    except Exception as e:
        logger.error(f"Error fetching opportunities: {e}")
        return []

@app.get("/api/applications/me")
async def get_my_applications(request: Request):
    """Get applications for the logged-in user"""
    try:
        from jose import jwt
        from backend.config import SECRET_KEY, ALGORITHM
        from backend.firebase_config import FirestoreCollections
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = auth_header[7:]
        
        # Decode token to get user info
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get applications from Firestore
        applications = firestore.query_documents(
            FirestoreCollections.APPLICATIONS,
            "user_id", "==", user_id
        )
        
        return applications or []
        
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        return []

@app.get("/api/jobs/temp")
async def get_temp_jobs(limit: int = 20):
    """Get temp/low-skill jobs with source URLs"""
    try:
        if job_storage:
            jobs = job_storage.get_temp_jobs(limit)
        else:
            # Fallback to immediate jobs
            jobs = recommendation_engine.get_immediate_jobs(limit)
        
        # Ensure source URLs
        for job in jobs:
            if not job.get('source_url') and job.get('url'):
                job['source_url'] = job['url']
        
        return jobs
    except Exception as e:
        logger.error(f"Error: {e}")
        return []

# Manual scraping triggers
@app.post("/api/scraping/trigger-scrape")
async def trigger_scrape():
    """Manually trigger job scraping"""
    try:
        if not job_storage:
            raise HTTPException(status_code=503, detail="Job storage not initialized")
        
        stats = job_storage.scrape_and_store_all()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scraping/status")
async def get_scraping_status():
    """Get scraping system status"""
    return {
        "job_storage": "available" if job_storage else "not initialized",
        "recommendation_engine": "available" if recommendation_engine else "not initialized",
        "firestore": "available" if firestore else "not initialized"
    }

# Application tracking
@app.post("/api/applications/track")
async def track_application(data: dict):
    """Track when user clicks apply button"""
    try:
        from backend.firebase_config import FirestoreCollections
        
        app_data = {
            "job_id": data.get('job_id'),
            "user_id": data.get('user_id'),
            "clicked_at": datetime.utcnow().isoformat(),
            "status": "redirected_to_source"
        }
        
        firestore.add_document(FirestoreCollections.APPLICATIONS, app_data)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error tracking application: {e}")
        return {"success": False, "error": str(e)}

# AI Chatbot endpoint with LangChain
@app.post("/api/chat")
async def chat_with_ai(data: dict):
    """
    GOPHORA AI Chatbot - Intelligent responses using LangChain + Gemini
    Can answer ANY question and provide job recommendations
    """
    try:
        message = data.get('message', '').strip()
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        logger.info(f"Chat query: {message}")
        
        # Use intelligent chatbot if available
        if intelligent_chatbot:
            response = await intelligent_chatbot.chat(message)
            return {
                "reply": response["response"],
                "opportunities": response["opportunities"],
                "ai_powered": response["ai_powered"]
            }
        else:
            # Fallback to simple response if chatbot not initialized
            return {
                "reply": "I'm currently in basic mode. To enable full AI capabilities, please set your GEMINI_API_KEY environment variable.",
                "opportunities": [],
                "ai_powered": False
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        
        # Ultimate fallback
        return {
            "reply": "I'm GOPHORA AI, your job search assistant! 🤖 Ask me about job opportunities, skills like Python or Java, remote work, temp jobs, or anything about GOPHORA. How can I help you today?",
            "opportunities": []
        }

# Legacy compatibility endpoints
@app.get("/api/opportunities/me")
async def get_my_opportunities():
    return []

@app.get("/api/opportunities/{opportunity_id}/applications")
async def get_applications(opportunity_id: str):
    return []

@app.post("/api/applications/apply")
async def apply(data: dict):
    """Legacy apply endpoint - now just tracks the click"""
    return await track_application(data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
