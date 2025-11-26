"""
Job Recommendation Engine
Provides personalized job matching based on user profile and AI embeddings
"""
import logging
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime

from .firebase_config import FirestoreHelper, FirestoreCollections
from .ai_validation import AIValidationPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobRecommendationEngine:
    """Recommends jobs to users based on their profile and preferences"""
    
    def __init__(self):
        self.firestore = FirestoreHelper()
        self.validator = AIValidationPipeline()
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def get_immediate_jobs(self, limit: int = 20) -> List[Dict]:
        """
        Get immediate, zero/low-skill jobs available to all users
        These are promoted jobs that anyone can start immediately
        """
        try:
            # Get from immediate jobs collection
            immediate_jobs = self.firestore.get_all_documents(
                FirestoreCollections.IMMEDIATE_JOBS,
                filters=[("approved", "==", True)],
                limit=limit
            )
            
            # Sort by trust score and recency
            immediate_jobs.sort(
                key=lambda x: (x.get("validation", {}).get("trust_score", 0), x.get("scraped_at", "")),
                reverse=True
            )
            
            return immediate_jobs
        except Exception as e:
            logger.error(f"Error getting immediate jobs: {e}")
            return []
    
    def get_skill_based_jobs(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get skill-based jobs matched to user's profile
        Uses embeddings for semantic matching
        """
        try:
            # Get user profile
            user_profiles = self.firestore.query_documents(
                FirestoreCollections.PROFILES,
                "user_id", "==", user_id
            )
            
            if not user_profiles:
                logger.warning(f"No profile found for user {user_id}")
                return []
            
            user_profile = user_profiles[0]
            user_skills = user_profile.get("skills", [])
            user_interests = user_profile.get("interests", [])
            
            # Create user embedding from skills and interests
            user_text = " ".join(user_skills + user_interests)
            user_embedding = self.validator.gemini_embeddings.embed_query(user_text)
            
            # Get all skill-based jobs
            skill_jobs = self.firestore.get_all_documents(
                FirestoreCollections.SKILL_BASED_JOBS,
                filters=[("approved", "==", True)]
            )
            
            # Calculate similarity scores
            scored_jobs = []
            for job in skill_jobs:
                job_embedding = job.get("embedding")
                if not job_embedding:
                    continue
                
                # Calculate semantic similarity
                similarity = self.cosine_similarity(user_embedding, job_embedding)
                
                # Boost score if user has required skills
                required_skills = job.get("metadata", {}).get("required_skills", [])
                skill_match_boost = 0
                for skill in user_skills:
                    if any(skill.lower() in req_skill.lower() for req_skill in required_skills):
                        skill_match_boost += 0.1
                
                total_score = similarity + skill_match_boost
                
                scored_jobs.append({
                    **job,
                    "match_score": total_score,
                    "similarity": similarity
                })
            
            # Sort by match score
            scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
            
            return scored_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error getting skill-based jobs for user {user_id}: {e}")
            return []
    
    def get_jobs_by_category(self, category: str, limit: int = 30) -> List[Dict]:
        """Get jobs filtered by category"""
        try:
            jobs = self.firestore.query_documents(
                FirestoreCollections.VERIFIED_JOBS,
                "category.primary_category", "==", category
            )
            
            # Filter approved only
            approved_jobs = [j for j in jobs if j.get("approved")]
            
            # Sort by trust score
            approved_jobs.sort(
                key=lambda x: x.get("validation", {}).get("trust_score", 0),
                reverse=True
            )
            
            return approved_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error getting jobs by category {category}: {e}")
            return []
    
    def search_jobs(self, query: str, limit: int = 30) -> List[Dict]:
        """
        Semantic search for jobs using embeddings
        """
        try:
            # Generate query embedding
            query_embedding = self.validator.gemini_embeddings.embed_query(query)
            
            # Get all verified jobs
            all_jobs = self.firestore.get_all_documents(
                FirestoreCollections.VERIFIED_JOBS,
                filters=[("approved", "==", True)]
            )
            
            # Calculate similarity scores
            scored_jobs = []
            for job in all_jobs:
                job_embedding = job.get("embedding")
                if not job_embedding:
                    continue
                
                similarity = self.cosine_similarity(query_embedding, job_embedding)
                
                scored_jobs.append({
                    **job,
                    "search_score": similarity
                })
            
            # Sort by search score
            scored_jobs.sort(key=lambda x: x["search_score"], reverse=True)
            
            return scored_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error searching jobs with query '{query}': {e}")
            return []
    
    def get_recommended_jobs_for_user(self, user_id: str) -> Dict[str, List[Dict]]:
        """
        Get comprehensive job recommendations for a user
        Returns both immediate jobs and personalized skill-based jobs
        """
        try:
            recommendations = {
                "immediate_jobs": self.get_immediate_jobs(limit=15),
                "skill_based_jobs": self.get_skill_based_jobs(user_id, limit=30),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {e}")
            return {
                "immediate_jobs": [],
                "skill_based_jobs": [],
                "error": str(e)
            }
    
    def get_jobs_by_location(self, location: str, limit: int = 30) -> List[Dict]:
        """Get jobs filtered by location"""
        try:
            # Query jobs with matching location
            jobs = self.firestore.get_all_documents(
                FirestoreCollections.VERIFIED_JOBS,
                filters=[("approved", "==", True)]
            )
            
            # Filter by location (case-insensitive partial match)
            location_jobs = [
                job for job in jobs 
                if location.lower() in job.get("location", "").lower()
            ]
            
            # Sort by trust score
            location_jobs.sort(
                key=lambda x: x.get("validation", {}).get("trust_score", 0),
                reverse=True
            )
            
            return location_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error getting jobs by location {location}: {e}")
            return []
    
    def get_trending_jobs(self, limit: int = 20) -> List[Dict]:
        """Get trending/popular jobs based on recency and trust score"""
        try:
            # Get recent approved jobs
            recent_jobs = self.firestore.get_all_documents(
                FirestoreCollections.VERIFIED_JOBS,
                filters=[("approved", "==", True)]
            )
            
            # Calculate trending score (recency + trust score)
            from datetime import datetime, timezone
            
            for job in recent_jobs:
                scraped_at = job.get("scraped_at", "")
                try:
                    if isinstance(scraped_at, str):
                        job_date = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                    else:
                        job_date = scraped_at
                    
                    hours_old = (datetime.now(timezone.utc) - job_date).total_seconds() / 3600
                    recency_score = max(0, 100 - hours_old)  # Newer = higher score
                except:
                    recency_score = 0
                
                trust_score = job.get("validation", {}).get("trust_score", 0)
                job["trending_score"] = (recency_score * 0.4) + (trust_score * 0.6)
            
            # Sort by trending score
            recent_jobs.sort(key=lambda x: x.get("trending_score", 0), reverse=True)
            
            return recent_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error getting trending jobs: {e}")
            return []
