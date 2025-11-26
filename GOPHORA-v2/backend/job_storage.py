"""
Job Storage Manager - Handles Firebase storage for scraped jobs
Stores jobs in separate collections:
- skill_based_jobs: Jobs requiring specific skills for user matching
- low_skill_temp_jobs: Entry-level, temporary, immediate start jobs
"""
from backend.firebase_config import FirestoreHelper, FirestoreCollections
from backend.job_scrapers import SkillBasedJobScraper, LowSkillTempJobScraper
import logging
from datetime import datetime
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStorageManager:
    """Manages storage of scraped jobs in Firebase"""
    
    def __init__(self):
        self.firestore = FirestoreHelper()
        self.skill_scraper = SkillBasedJobScraper()
        self.temp_scraper = LowSkillTempJobScraper()
    
    def store_skill_based_jobs(self, jobs: List[Dict]) -> int:
        """
        Store skill-based jobs in Firebase
        Returns: Number of jobs successfully stored
        """
        stored_count = 0
        
        for job in jobs:
            try:
                # Check if job already exists (by URL)
                existing = self.firestore.query_documents(
                    FirestoreCollections.SKILL_BASED_JOBS,
                    'source_url',
                    '==',
                    job.get('source_url', '')
                )
                
                if existing:
                    logger.info(f"Job already exists: {job.get('title')} - skipping")
                    continue
                
                # Add metadata
                job['stored_at'] = datetime.utcnow().isoformat()
                job['status'] = 'active'
                job['views'] = 0
                job['applications'] = 0
                
                # Store in Firebase
                doc_id = self.firestore.add_document(
                    FirestoreCollections.SKILL_BASED_JOBS,
                    job
                )
                
                logger.info(f"Stored skill-based job: {job.get('title')} (ID: {doc_id})")
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Error storing skill-based job: {e}")
        
        logger.info(f"Stored {stored_count}/{len(jobs)} skill-based jobs")
        return stored_count
    
    def store_temp_jobs(self, jobs: List[Dict]) -> int:
        """
        Store low-skill/temp jobs in Firebase
        Returns: Number of jobs successfully stored
        """
        stored_count = 0
        
        for job in jobs:
            try:
                # Check if job already exists (by URL)
                existing = self.firestore.query_documents(
                    FirestoreCollections.IMMEDIATE_JOBS,
                    'source_url',
                    '==',
                    job.get('source_url', '')
                )
                
                if existing:
                    logger.info(f"Temp job already exists: {job.get('title')} - skipping")
                    continue
                
                # Add metadata
                job['stored_at'] = datetime.utcnow().isoformat()
                job['status'] = 'active'
                job['views'] = 0
                job['applications'] = 0
                job['approved'] = True  # Auto-approve temp/entry jobs
                
                # Store in Firebase (using IMMEDIATE_JOBS collection for temp jobs)
                doc_id = self.firestore.add_document(
                    FirestoreCollections.IMMEDIATE_JOBS,
                    job
                )
                
                logger.info(f"Stored temp job: {job.get('title')} (ID: {doc_id})")
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Error storing temp job: {e}")
        
        logger.info(f"Stored {stored_count}/{len(jobs)} temp jobs")
        return stored_count
    
    def scrape_and_store_skill_jobs(self, skills: List[str] = None) -> Dict:
        """
        Scrape skill-based jobs and store in Firebase
        Returns: Statistics about the operation
        """
        logger.info(f"Starting skill-based job scraping for skills: {skills or 'all'}")
        
        # Scrape jobs
        jobs = self.skill_scraper.scrape_all_skills(skills)
        
        # Store in Firebase
        stored_count = self.store_skill_based_jobs(jobs)
        
        stats = {
            'total_scraped': len(jobs),
            'total_stored': stored_count,
            'duplicates_skipped': len(jobs) - stored_count,
            'skills_queried': skills or ['general'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log scraping activity
        self._log_scraping_activity('skill_based', stats)
        
        return stats
    
    def scrape_and_store_temp_jobs(self) -> Dict:
        """
        Scrape low-skill/temp jobs and store in Firebase
        Returns: Statistics about the operation
        """
        logger.info("Starting low-skill/temp job scraping")
        
        # Scrape jobs
        jobs = self.temp_scraper.scrape_all_temp_jobs()
        
        # Store in Firebase
        stored_count = self.store_temp_jobs(jobs)
        
        stats = {
            'total_scraped': len(jobs),
            'total_stored': stored_count,
            'duplicates_skipped': len(jobs) - stored_count,
            'job_type': 'low_skill_temp',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log scraping activity
        self._log_scraping_activity('low_skill_temp', stats)
        
        return stats
    
    def scrape_and_store_all(self, skills: List[str] = None) -> Dict:
        """
        Scrape both skill-based and temp jobs, store in Firebase
        Returns: Combined statistics
        """
        logger.info("Starting comprehensive job scraping...")
        
        # Scrape skill-based jobs
        skill_stats = self.scrape_and_store_skill_jobs(skills)
        
        # Scrape temp jobs
        temp_stats = self.scrape_and_store_temp_jobs()
        
        combined_stats = {
            'skill_based_jobs': skill_stats,
            'temp_jobs': temp_stats,
            'total_scraped': skill_stats['total_scraped'] + temp_stats['total_scraped'],
            'total_stored': skill_stats['total_stored'] + temp_stats['total_stored'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Scraping complete - Total stored: {combined_stats['total_stored']} jobs")
        
        return combined_stats
    
    def get_jobs_for_user_skills(self, user_skills: List[str], limit: int = 20) -> List[Dict]:
        """
        Get skill-based jobs matching user's skills
        Returns: List of matching jobs
        """
        if not user_skills:
            # Return general jobs if no skills provided
            return self.firestore.get_all_documents(
                FirestoreCollections.SKILL_BASED_JOBS,
                filters=[('status', '==', 'active')],
                limit=limit
            )
        
        # Query jobs that match any of the user's skills
        matching_jobs = []
        
        for skill in user_skills:
            jobs = self.firestore.get_all_documents(
                FirestoreCollections.SKILL_BASED_JOBS,
                filters=[
                    ('status', '==', 'active'),
                    # Note: Firestore array-contains only works for exact matches
                ],
                limit=limit
            )
            
            # Filter jobs that contain the skill
            for job in jobs:
                job_skills = job.get('skills', [])
                job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
                
                if skill.lower() in [s.lower() for s in job_skills] or skill.lower() in job_text:
                    matching_jobs.append(job)
        
        # Remove duplicates and limit
        unique_jobs = {job['id']: job for job in matching_jobs}.values()
        return list(unique_jobs)[:limit]
    
    def get_temp_jobs(self, limit: int = 20) -> List[Dict]:
        """
        Get low-skill/temp jobs
        Returns: List of temp jobs
        """
        return self.firestore.get_all_documents(
            FirestoreCollections.IMMEDIATE_JOBS,
            filters=[('status', '==', 'active'), ('job_category', '==', 'low_skill_temp')],
            limit=limit
        )
    
    def get_all_immediate_jobs(self, limit: int = 50) -> List[Dict]:
        """
        Get all immediate/entry-level jobs (both temp and entry skill-based)
        Returns: List of immediate jobs
        """
        temp_jobs = self.get_temp_jobs(limit)
        
        # Also get entry-level skill-based jobs
        entry_skill_jobs = self.firestore.get_all_documents(
            FirestoreCollections.SKILL_BASED_JOBS,
            filters=[
                ('status', '==', 'active'),
                ('experience_level', '==', 'Entry')
            ],
            limit=limit
        )
        
        all_jobs = temp_jobs + entry_skill_jobs
        return all_jobs[:limit]
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Mark old jobs as inactive
        Returns: Number of jobs cleaned up
        """
        from datetime import timedelta
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cleaned = 0
        
        # Cleanup skill-based jobs
        old_skill_jobs = self.firestore.get_all_documents(
            FirestoreCollections.SKILL_BASED_JOBS,
            filters=[('status', '==', 'active')]
        )
        
        for job in old_skill_jobs:
            if job.get('scraped_at', '') < cutoff_date:
                self.firestore.update_document(
                    FirestoreCollections.SKILL_BASED_JOBS,
                    job['id'],
                    {'status': 'inactive', 'inactive_date': datetime.utcnow().isoformat()}
                )
                cleaned += 1
        
        # Cleanup temp jobs
        old_temp_jobs = self.firestore.get_all_documents(
            FirestoreCollections.IMMEDIATE_JOBS,
            filters=[('status', '==', 'active')]
        )
        
        for job in old_temp_jobs:
            if job.get('scraped_at', '') < cutoff_date:
                self.firestore.update_document(
                    FirestoreCollections.IMMEDIATE_JOBS,
                    job['id'],
                    {'status': 'inactive', 'inactive_date': datetime.utcnow().isoformat()}
                )
                cleaned += 1
        
        logger.info(f"Marked {cleaned} old jobs as inactive")
        return cleaned
    
    def _log_scraping_activity(self, job_type: str, stats: Dict):
        """Log scraping activity to Firebase"""
        try:
            log_data = {
                'job_type': job_type,
                'stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.firestore.add_document(
                FirestoreCollections.SCRAPING_LOGS,
                log_data
            )
        except Exception as e:
            logger.error(f"Error logging scraping activity: {e}")


# CLI for manual scraping
if __name__ == "__main__":
    import sys
    
    manager = JobStorageManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "skill":
            skills = sys.argv[2:] if len(sys.argv) > 2 else None
            print(f"Scraping skill-based jobs for: {skills or 'all skills'}")
            stats = manager.scrape_and_store_skill_jobs(skills)
            print(f"\nResults: {stats}")
        
        elif command == "temp":
            print("Scraping low-skill/temp jobs...")
            stats = manager.scrape_and_store_temp_jobs()
            print(f"\nResults: {stats}")
        
        elif command == "all":
            skills = sys.argv[2:] if len(sys.argv) > 2 else None
            print(f"Scraping all job types...")
            stats = manager.scrape_and_store_all(skills)
            print(f"\nResults: {stats}")
        
        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            print(f"Cleaning up jobs older than {days} days...")
            cleaned = manager.cleanup_old_jobs(days)
            print(f"Cleaned up {cleaned} jobs")
        
        else:
            print("Unknown command. Use: skill, temp, all, or cleanup")
    
    else:
        print("Usage:")
        print("  python job_storage.py skill [skill1] [skill2] ...")
        print("  python job_storage.py temp")
        print("  python job_storage.py all [skill1] [skill2] ...")
        print("  python job_storage.py cleanup [days]")
