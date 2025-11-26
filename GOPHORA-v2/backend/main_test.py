"""
Minimal test version of main.py to verify Firebase connection
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GOPHORA AI Backend - Test", version="2.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Test Firebase connection on startup"""
    try:
        logger.info("Testing Firebase connection...")
        from backend.firebase_config import initialize_firebase, get_firestore_db
        initialize_firebase()
        db = get_firestore_db()
        logger.info("✅ Firebase connected successfully!")
    except Exception as e:
        logger.error(f"❌ Firebase connection failed: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "GOPHORA AI Backend",
        "version": "2.0 - Test"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "firebase": "checking..."
    }

@app.get("/test-firebase")
async def test_firebase():
    """Test Firebase operations"""
    try:
        from backend.firebase_config import FirestoreHelper, FirestoreCollections
        from datetime import datetime
        
        firestore = FirestoreHelper()
        
        # Test write
        test_data = {
            "message": "Test from GOPHORA",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        doc_id = firestore.add_document("test_collection", test_data)
        
        # Test read
        doc = firestore.get_document("test_collection", doc_id)
        
        return {
            "success": True,
            "message": "Firebase read/write successful",
            "data": doc
        }
    except Exception as e:
        logger.error(f"Firebase test error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
