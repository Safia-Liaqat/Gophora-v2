"""
Firebase Configuration and Firestore Setup
Manages Firebase Admin SDK initialization and Firestore collections
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        print("Firebase already initialized")
    except ValueError:
        # Path to your Firebase service account key JSON file
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully with credentials file")
        else:
            # Alternative: Initialize with environment variables
            firebase_config = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
            }
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully with environment variables")

# Get Firestore client
def get_firestore_db():
    """Get Firestore database client"""
    return firestore.client()

# Initialize Firebase on module import
initialize_firebase()
db = get_firestore_db()

# Firestore Collections
class FirestoreCollections:
    """Firestore collection names"""
    USERS = "users"
    PROFILES = "profiles"
    OPPORTUNITIES = "opportunities"
    APPLICATIONS = "applications"
    SUBSCRIPTIONS = "subscriptions"
    SCRAPED_JOBS = "scraped_jobs"  # Raw scraped data
    VERIFIED_JOBS = "verified_jobs"  # AI-verified jobs
    IMMEDIATE_JOBS = "immediate_jobs"  # Zero/low-skill jobs
    SKILL_BASED_JOBS = "skill_based_jobs"  # Skill-required jobs
    SCRAPING_LOGS = "scraping_logs"  # Scraping activity logs
    VALIDATION_LOGS = "validation_logs"  # AI validation logs

# Helper functions for Firestore operations
class FirestoreHelper:
    """Helper class for common Firestore operations"""
    
    @staticmethod
    def add_document(collection_name: str, data: dict, doc_id: str = None):
        """Add a document to a collection"""
        collection = db.collection(collection_name)
        if doc_id:
            doc_ref = collection.document(doc_id)
            doc_ref.set(data)
            return doc_id
        else:
            doc_ref = collection.add(data)
            return doc_ref[1].id
    
    @staticmethod
    def get_document(collection_name: str, doc_id: str):
        """Get a document by ID"""
        doc_ref = db.collection(collection_name).document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return {"id": doc.id, **doc.to_dict()}
        return None
    
    @staticmethod
    def update_document(collection_name: str, doc_id: str, data: dict):
        """Update a document"""
        doc_ref = db.collection(collection_name).document(doc_id)
        doc_ref.update(data)
        return True
    
    @staticmethod
    def delete_document(collection_name: str, doc_id: str):
        """Delete a document"""
        db.collection(collection_name).document(doc_id).delete()
        return True
    
    @staticmethod
    def get_all_documents(collection_name: str, filters: list = None, limit: int = None):
        """Get all documents from a collection with optional filters"""
        query = db.collection(collection_name)
        
        if filters:
            for field, operator, value in filters:
                query = query.where(field, operator, value)
        
        if limit:
            query = query.limit(limit)
        
        docs = query.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    
    @staticmethod
    def query_documents(collection_name: str, field: str, operator: str, value):
        """Query documents by field"""
        docs = db.collection(collection_name).where(field, operator, value).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    
    @staticmethod
    def batch_write(operations: list):
        """Perform batch write operations"""
        batch = db.batch()
        for op in operations:
            if op["type"] == "set":
                doc_ref = db.collection(op["collection"]).document(op.get("doc_id"))
                batch.set(doc_ref, op["data"])
            elif op["type"] == "update":
                doc_ref = db.collection(op["collection"]).document(op["doc_id"])
                batch.update(doc_ref, op["data"])
            elif op["type"] == "delete":
                doc_ref = db.collection(op["collection"]).document(op["doc_id"])
                batch.delete(doc_ref)
        batch.commit()
        return True
