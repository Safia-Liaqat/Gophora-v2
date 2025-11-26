"""
Automated Job Scraping Scheduler
Runs 24/7 to continuously scrape and store jobs
- Skill-based jobs: Every 15 minutes
- Temp/low-skill jobs: Every 15 minutes (offset)
- Cleanup old jobs: Daily
"""
from apscheduler.schedulers.background import BackgroundScheduler
from backend.job_storage import JobStorageManager
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutomatedJobScheduler:
    """Manages automated job scraping on schedules"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.storage_manager = JobStorageManager()
        self.is_running = False
        
        # Common skills to scrape for
        self.common_skills = [
            'python', 'javascript', 'java', 'react', 'node.js',
            'sql', 'aws', 'docker', 'machine learning', 'data science',
            'customer service', 'marketing', 'sales', 'design', 'writing'
        ]
    
    def scrape_skill_jobs_task(self):
        """Task to scrape skill-based jobs"""
        try:
            logger.info(f"[SCHEDULER] Starting skill-based job scraping at {datetime.utcnow()}")
            stats = self.storage_manager.scrape_and_store_skill_jobs(self.common_skills)
            logger.info(f"[SCHEDULER] Skill-based scraping complete: {stats}")
        except Exception as e:
            logger.error(f"[SCHEDULER] Error in skill job scraping: {e}")
    
    def scrape_temp_jobs_task(self):
        """Task to scrape temp/low-skill jobs"""
        try:
            logger.info(f"[SCHEDULER] Starting temp job scraping at {datetime.utcnow()}")
            stats = self.storage_manager.scrape_and_store_temp_jobs()
            logger.info(f"[SCHEDULER] Temp job scraping complete: {stats}")
        except Exception as e:
            logger.error(f"[SCHEDULER] Error in temp job scraping: {e}")
    
    def cleanup_jobs_task(self):
        """Task to cleanup old jobs"""
        try:
            logger.info(f"[SCHEDULER] Starting job cleanup at {datetime.utcnow()}")
            cleaned = self.storage_manager.cleanup_old_jobs(days=30)
            logger.info(f"[SCHEDULER] Cleanup complete: {cleaned} jobs marked inactive")
        except Exception as e:
            logger.error(f"[SCHEDULER] Error in cleanup: {e}")
    
    def start(self):
        """Start the automated scheduler - scrapes every 15 minutes"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule skill-based job scraping every 15 minutes
        self.scheduler.add_job(
            func=self.scrape_skill_jobs_task,
            trigger='interval',
            minutes=15,
            id='scrape_skill_jobs',
            name='Scrape skill-based jobs (every 15 min)',
            replace_existing=True
        )
        
        # Schedule temp job scraping every 15 minutes (offset by 7 minutes)
        self.scheduler.add_job(
            func=self.scrape_temp_jobs_task,
            trigger='interval',
            minutes=15,
            id='scrape_temp_jobs',
            name='Scrape temp/low-skill jobs (every 15 min)',
            replace_existing=True,
            next_run_time=datetime.now() + timedelta(minutes=7)  # Start 7 min after skill jobs
        )
        
        # Schedule cleanup daily at 2 AM
        self.scheduler.add_job(
            func=self.cleanup_jobs_task,
            trigger='cron',
            hour=2,
            minute=0,
            id='cleanup_jobs',
            name='Cleanup old jobs',
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info("✅ Automated job scraping scheduler started!")
        logger.info("📅 Skill-based jobs: Every 15 minutes")
        logger.info("📅 Temp jobs: Every 15 minutes (offset)")
        logger.info("📅 Cleanup: Daily at 2 AM")
        logger.info("   - Skill-based jobs: Every 6 hours")
        logger.info("   - Temp/low-skill jobs: Every 3 hours")
        logger.info("   - Cleanup: Daily at 2 AM")
        
        # Schedule initial scraping to run after 30 seconds (non-blocking)
        logger.info("Initial scraping will start in 30 seconds (non-blocking)...")
        import threading
        def delayed_initial_scrape():
            import time
            time.sleep(30)
            logger.info("Running initial scraping...")
            self.scrape_skill_jobs_task()
            self.scrape_temp_jobs_task()
        
        scrape_thread = threading.Thread(target=delayed_initial_scrape, daemon=True)
        scrape_thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")
    
    def get_status(self):
        """Get scheduler status and job info"""
        if not self.is_running:
            return {"status": "stopped"}
        
        jobs = self.scheduler.get_jobs()
        return {
            "status": "running",
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None
                }
                for job in jobs
            ]
        }


# Standalone script for testing
if __name__ == "__main__":
    import time
    
    scheduler = AutomatedJobScheduler()
    
    print("Starting automated job scraping scheduler...")
    print("Press Ctrl+C to stop\n")
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(60)
            status = scheduler.get_status()
            print(f"\nScheduler Status: {status['status']}")
            if status['status'] == 'running':
                for job in status['jobs']:
                    print(f"  - {job['name']}: Next run at {job['next_run']}")
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped")
