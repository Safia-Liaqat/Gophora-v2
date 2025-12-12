# functions/main.py

from firebase_admin import initialize_app, get_app, credentials
from firebase_functions import https_fn

# Assuming your FastAPI object is named 'app' inside 'backend/main.py'
from backend.main import app

# =========================================================================
# 1. Firebase Initialization Fix (Automatic Cloud Credentials)
# =========================================================================
try:
    # Attempt to retrieve the default app.
    get_app(name='[DEFAULT]')
except ValueError:
    # Initialize using Application Default Credentials (for secure cloud execution)
    initialize_app(credentials=credentials.ApplicationDefault()) 


# =========================================================================
# 2. FastAPI/ASGI Crash Fix
# =========================================================================
@https_fn.on_request(
    region="us-central1", 
    secrets=["JWT_SECRET", "GEMINI_API_KEY"]
)
def api_server(req: https_fn.Request) -> https_fn.Response:
    """
    Handles HTTP requests by passing the request object to the FastAPI (ASGI) application.
    The req.get_response(app) method correctly translates the Flask/Functions 
    request format into the ASGI format (scope, receive, send) that FastAPI needs.
    """
    # This line replaces 'return app(req)' which caused the TypeError.
    return ap(req)