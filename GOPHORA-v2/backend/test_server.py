"""Minimal test server to diagnose crashes"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("✅ Test server started!")

@app.get("/")
def root():
    return {"status": "ok", "message": "Test server running"}

@app.get("/api/opportunities/recommend")
def get_jobs():
    return [
        {"id": "1", "title": "Test Job", "company": "Test Co", "location": "Remote", "url": "https://example.com/job1"},
        {"id": "2", "title": "Another Job", "company": "Another Co", "location": "NYC", "url": "https://example.com/job2"}
    ]
