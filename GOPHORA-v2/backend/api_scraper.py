"""
API-based Job Scraper - Uses legitimate job APIs
No web scraping blocks - uses official APIs
"""
import requests
import logging
from datetime import datetime
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealJobScraper:
    """Scrapes jobs from APIs that allow access"""
    
    def __init__(self):
        self.headers = {'User-Agent': 'GOPHORA Job Aggregator'}
    
    def scrape_remotive(self) -> List[Dict]:
        """Scrape from Remotive API - allows free access"""
        jobs = []
        try:
            url = "https://remotive.com/api/remote-jobs"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('jobs', [])[:20]:  # Get first 20
                jobs.append({
                    'title': job.get('title', ''),
                    'company': job.get('company_name', ''),
                    'location': 'Remote',
                    'description': job.get('description', '')[:500],
                    'job_type': job.get('job_type', 'Full-time'),
                    'salary': job.get('salary', 'Not specified'),
                    'requirements': job.get('description', '')[:300],
                    'url': job.get('url', ''),
                    'source': 'Remotive',
                    'scraped_at': datetime.utcnow().isoformat(),
                    'category': job.get('category', 'General'),
                    'tags': job.get('tags', [])
                })
            
            logger.info(f"Scraped {len(jobs)} jobs from Remotive API")
        except Exception as e:
            logger.error(f"Error scraping Remotive: {e}")
        
        return jobs
    
    def scrape_github_jobs(self) -> List[Dict]:
        """Scrape GitHub Jobs (maintained community version)"""
        jobs = []
        try:
            url = "https://www.arbeitnow.com/api/job-board-api"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('data', [])[:15]:
                jobs.append({
                    'title': job.get('title', ''),
                    'company': job.get('company_name', ''),
                    'location': job.get('location', 'Remote'),
                    'description': job.get('description', '')[:500],
                    'job_type': 'Full-time',
                    'salary': 'Competitive',
                    'requirements': job.get('description', '')[:300],
                    'url': job.get('url', ''),
                    'source': 'Arbeitnow',
                    'scraped_at': datetime.utcnow().isoformat(),
                    'tags': job.get('tags', [])
                })
            
            logger.info(f"Scraped {len(jobs)} jobs from Arbeitnow API")
        except Exception as e:
            logger.error(f"Error scraping Arbeitnow: {e}")
        
        return jobs
    
    def scrape_usajobs(self) -> List[Dict]:
        """Scrape USAJobs.gov API - Government jobs, public API"""
        jobs = []
        try:
            url = "https://data.usajobs.gov/api/search"
            headers = {
                **self.headers,
                'Host': 'data.usajobs.gov',
                'Authorization-Key': 'YOUR_API_KEY_HERE'  # Free API key
            }
            params = {
                'Keyword': 'entry level',
                'ResultsPerPage': 15
            }
            
            # Note: Requires free API key from usajobs.gov
            # Skipping for now
            logger.info("USAJobs requires API key - skipping")
        except Exception as e:
            logger.error(f"Error scraping USAJobs: {e}")
        
        return jobs
    
    def scrape_all(self) -> List[Dict]:
        """Scrape from all available sources"""
        all_jobs = []
        
        # Scrape Remotive
        remotive_jobs = self.scrape_remotive()
        all_jobs.extend(remotive_jobs)
        
        # Scrape Arbeitnow
        arbeitnow_jobs = self.scrape_github_jobs()
        all_jobs.extend(arbeitnow_jobs)
        
        logger.info(f"Total jobs scraped: {len(all_jobs)}")
        return all_jobs


if __name__ == "__main__":
    scraper = RealJobScraper()
    jobs = scraper.scrape_all()
    print(f"Scraped {len(jobs)} jobs!")
    for job in jobs[:3]:
        print(f"- {job['title']} at {job['company']}")
