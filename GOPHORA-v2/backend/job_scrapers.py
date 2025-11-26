"""
High-Quality Job Scraping System
- Skill-based jobs for user matching
- Low-skill/temp jobs for immediate opportunities
- Stores source URLs for apply redirects
- Multiple APIs + web scraping fallback
"""
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict, Optional
import time
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkillBasedJobScraper:
    """Scrapes jobs requiring specific skills for user matching"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
    
    def scrape_remotive_by_skill(self, skill: str = None) -> List[Dict]:
        """Scrape Remotive API filtered by skill/category"""
        jobs = []
        try:
            url = "https://remotive.com/api/remote-jobs"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('jobs', []):
                # Filter by skill if provided
                if skill:
                    job_text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('tags', []))}".lower()
                    if skill.lower() not in job_text:
                        continue
                
                jobs.append({
                    'title': job.get('title', ''),
                    'company': job.get('company_name', ''),
                    'location': job.get('candidate_required_location', 'Remote'),
                    'description': job.get('description', ''),
                    'job_type': job.get('job_type', 'Full-time'),
                    'salary': job.get('salary', 'Not specified'),
                    'requirements': self._extract_requirements(job.get('description', '')),
                    'skills': job.get('tags', []),
                    'experience_level': self._determine_experience_level(job),
                    'url': job.get('url', ''),
                    'source': 'Remotive',
                    'source_url': job.get('url', ''),  # Direct application link
                    'scraped_at': datetime.utcnow().isoformat(),
                    'category': job.get('category', 'General'),
                    'job_category': 'skill_based',
                    'posted_date': job.get('publication_date', datetime.utcnow().isoformat())
                })
            
            logger.info(f"Scraped {len(jobs)} skill-based jobs from Remotive" + (f" for skill: {skill}" if skill else ""))
        except Exception as e:
            logger.error(f"Error scraping Remotive for skills: {e}")
        
        return jobs
    
    def scrape_adzuna_api(self, skill: str = None, country: str = "us") -> List[Dict]:
        """Scrape Adzuna API - free API with skill filtering"""
        jobs = []
        try:
            # Adzuna API (requires free API key from https://developer.adzuna.com/)
            # For now, using public endpoint
            app_id = "YOUR_ADZUNA_APP_ID"  # Get free at developer.adzuna.com
            app_key = "YOUR_ADZUNA_API_KEY"
            
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
            params = {
                'app_id': app_id,
                'app_key': app_key,
                'results_per_page': 50,
                'what': skill if skill else 'developer',
                'content-type': 'application/json'
            }
            
            # Skip if no API keys configured
            if "YOUR_" in app_id:
                logger.info("Adzuna API keys not configured - skipping")
                return jobs
            
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('results', []):
                jobs.append({
                    'title': job.get('title', ''),
                    'company': job.get('company', {}).get('display_name', 'Not specified'),
                    'location': job.get('location', {}).get('display_name', 'Remote'),
                    'description': job.get('description', ''),
                    'job_type': job.get('contract_time', 'Full-time'),
                    'salary': f"${job.get('salary_min', 0)} - ${job.get('salary_max', 0)}" if job.get('salary_min') else 'Not specified',
                    'requirements': self._extract_requirements(job.get('description', '')),
                    'skills': self._extract_skills_from_text(job.get('description', '')),
                    'experience_level': self._determine_experience_from_text(job.get('description', '')),
                    'url': job.get('redirect_url', ''),
                    'source': 'Adzuna',
                    'source_url': job.get('redirect_url', ''),
                    'scraped_at': datetime.utcnow().isoformat(),
                    'category': job.get('category', {}).get('label', 'General'),
                    'job_category': 'skill_based',
                    'posted_date': job.get('created', datetime.utcnow().isoformat())
                })
            
            logger.info(f"Scraped {len(jobs)} jobs from Adzuna")
        except Exception as e:
            logger.error(f"Error scraping Adzuna: {e}")
        
        return jobs
    
    def scrape_github_jobs_api(self, skill: str = None) -> List[Dict]:
        """Scrape GitHub Jobs via Arbeitnow API with skill filtering"""
        jobs = []
        try:
            url = "https://www.arbeitnow.com/api/job-board-api"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('data', []):
                # Filter by skill if provided
                if skill:
                    job_text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('tags', []))}".lower()
                    if skill.lower() not in job_text:
                        continue
                
                jobs.append({
                    'title': job.get('title', ''),
                    'company': job.get('company_name', ''),
                    'location': job.get('location', 'Remote'),
                    'description': job.get('description', ''),
                    'job_type': 'Full-time',
                    'salary': 'Competitive',
                    'requirements': self._extract_requirements(job.get('description', '')),
                    'skills': job.get('tags', []),
                    'experience_level': self._determine_experience_from_text(job.get('description', '')),
                    'url': job.get('url', ''),
                    'source': 'Arbeitnow',
                    'source_url': job.get('url', ''),
                    'scraped_at': datetime.utcnow().isoformat(),
                    'category': 'Tech',
                    'job_category': 'skill_based',
                    'posted_date': job.get('created_at', datetime.utcnow().isoformat())
                })
            
            logger.info(f"Scraped {len(jobs)} skill-based jobs from Arbeitnow")
        except Exception as e:
            logger.error(f"Error scraping Arbeitnow: {e}")
        
        return jobs
    
    def scrape_findwork_api(self, skill: str = None) -> List[Dict]:
        """Scrape Findwork.dev API - free remote jobs"""
        jobs = []
        try:
            url = "https://findwork.dev/api/jobs/"
            headers = {
                **self.headers,
                'Authorization': 'Token YOUR_FINDWORK_API_KEY'  # Free at findwork.dev
            }
            
            params = {'search': skill} if skill else {}
            
            # Skip if no API key
            if "YOUR_" in headers['Authorization']:
                logger.info("Findwork API key not configured - skipping")
                return jobs
            
            response = self.session.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('results', []):
                jobs.append({
                    'title': job.get('role', ''),
                    'company': job.get('company_name', ''),
                    'location': job.get('location', 'Remote'),
                    'description': job.get('text', ''),
                    'job_type': job.get('employment_type', 'Full-time'),
                    'salary': 'Not specified',
                    'requirements': self._extract_requirements(job.get('text', '')),
                    'skills': job.get('keywords', []),
                    'experience_level': self._determine_experience_from_text(job.get('text', '')),
                    'url': job.get('url', ''),
                    'source': 'Findwork',
                    'source_url': job.get('url', ''),
                    'scraped_at': datetime.utcnow().isoformat(),
                    'category': 'Tech',
                    'job_category': 'skill_based',
                    'posted_date': job.get('date_posted', datetime.utcnow().isoformat())
                })
            
            logger.info(f"Scraped {len(jobs)} jobs from Findwork")
        except Exception as e:
            logger.error(f"Error scraping Findwork: {e}")
        
        return jobs
    
    def scrape_all_skills(self, skills: List[str] = None) -> List[Dict]:
        """Scrape all sources for skill-based jobs"""
        all_jobs = []
        
        if not skills:
            skills = [None]  # Get general jobs
        
        for skill in skills:
            # Scrape from all sources
            all_jobs.extend(self.scrape_remotive_by_skill(skill))
            all_jobs.extend(self.scrape_github_jobs_api(skill))
            all_jobs.extend(self.scrape_adzuna_api(skill))
            all_jobs.extend(self.scrape_findwork_api(skill))
            
            time.sleep(1)  # Rate limiting between skills
        
        # Remove duplicates based on URL
        unique_jobs = {job['url']: job for job in all_jobs if job.get('url')}.values()
        unique_jobs = list(unique_jobs)
        
        logger.info(f"Total unique skill-based jobs: {len(unique_jobs)}")
        return unique_jobs
    
    def _extract_requirements(self, description: str) -> str:
        """Extract requirements section from job description"""
        if not description:
            return ""
        
        # Look for requirements section
        patterns = [
            r'(?:requirements?|qualifications?|what we.*looking for)[\s\S]{0,500}',
            r'(?:you should have|you will need|must have)[\s\S]{0,300}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)[:500]
        
        return description[:300]
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skill keywords from text"""
        common_skills = [
            'python', 'javascript', 'java', 'react', 'node', 'sql', 'aws', 
            'docker', 'kubernetes', 'git', 'agile', 'scrum', 'rest', 'api',
            'typescript', 'vue', 'angular', 'mongodb', 'postgresql', 'redis',
            'machine learning', 'ai', 'data science', 'devops', 'ci/cd'
        ]
        
        text_lower = text.lower()
        found_skills = [skill for skill in common_skills if skill in text_lower]
        return found_skills[:10]  # Limit to top 10
    
    def _determine_experience_level(self, job: Dict) -> str:
        """Determine experience level from job data"""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        
        if any(word in title or word in description for word in ['senior', 'lead', 'principal', 'architect']):
            return 'Senior'
        elif any(word in title or word in description for word in ['junior', 'entry', 'graduate', 'intern']):
            return 'Entry'
        else:
            return 'Mid-level'
    
    def _determine_experience_from_text(self, text: str) -> str:
        """Determine experience level from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['senior', 'lead', 'principal', 'architect', '5+ years', '7+ years']):
            return 'Senior'
        elif any(word in text_lower for word in ['junior', 'entry', 'graduate', 'intern', '0-2 years', 'no experience']):
            return 'Entry'
        else:
            return 'Mid-level'


class LowSkillTempJobScraper:
    """Scrapes low-skill, temporary, and immediate start jobs"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
    
    def scrape_remotive_entry_level(self) -> List[Dict]:
        """Scrape entry-level and immediate jobs from Remotive"""
        jobs = []
        try:
            url = "https://remotive.com/api/remote-jobs"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            entry_keywords = ['entry', 'junior', 'no experience', 'trainee', 'intern', 'customer service', 
                            'data entry', 'virtual assistant', 'support', 'beginner']
            
            for job in data.get('jobs', []):
                job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
                
                # Filter for entry-level/low-skill jobs
                if any(keyword in job_text for keyword in entry_keywords):
                    jobs.append({
                        'title': job.get('title', ''),
                        'company': job.get('company_name', ''),
                        'location': 'Remote',
                        'description': job.get('description', '')[:500],
                        'job_type': job.get('job_type', 'Full-time'),
                        'salary': job.get('salary', 'Not specified'),
                        'requirements': 'Minimal experience required',
                        'skills': job.get('tags', []),
                        'experience_level': 'Entry',
                        'url': job.get('url', ''),
                        'source': 'Remotive',
                        'source_url': job.get('url', ''),
                        'scraped_at': datetime.utcnow().isoformat(),
                        'category': job.get('category', 'General'),
                        'job_category': 'low_skill_temp',
                        'immediate_start': True,
                        'posted_date': job.get('publication_date', datetime.utcnow().isoformat())
                    })
            
            logger.info(f"Scraped {len(jobs)} low-skill jobs from Remotive")
        except Exception as e:
            logger.error(f"Error scraping Remotive entry jobs: {e}")
        
        return jobs
    
    def scrape_snagajob_api(self) -> List[Dict]:
        """Scrape hourly/temp jobs (Snagajob-style)"""
        jobs = []
        try:
            # Note: Snagajob doesn't have public API, using Arbeitnow as alternative
            url = "https://www.arbeitnow.com/api/job-board-api"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            temp_keywords = ['hourly', 'part-time', 'temporary', 'contract', 'freelance', 'gig']
            
            for job in data.get('data', [])[:20]:
                job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
                
                if any(keyword in job_text for keyword in temp_keywords):
                    jobs.append({
                        'title': job.get('title', ''),
                        'company': job.get('company_name', ''),
                        'location': job.get('location', 'Remote'),
                        'description': job.get('description', '')[:500],
                        'job_type': 'Part-time/Temporary',
                        'salary': 'Hourly',
                        'requirements': 'Basic skills required',
                        'skills': job.get('tags', []),
                        'experience_level': 'Entry',
                        'url': job.get('url', ''),
                        'source': 'Arbeitnow',
                        'source_url': job.get('url', ''),
                        'scraped_at': datetime.utcnow().isoformat(),
                        'category': 'Temporary',
                        'job_category': 'low_skill_temp',
                        'immediate_start': True,
                        'posted_date': job.get('created_at', datetime.utcnow().isoformat())
                    })
            
            logger.info(f"Scraped {len(jobs)} temp jobs from Arbeitnow")
        except Exception as e:
            logger.error(f"Error scraping temp jobs: {e}")
        
        return jobs
    
    def scrape_usajobs_entry(self) -> List[Dict]:
        """Scrape entry-level government jobs from USAJobs"""
        jobs = []
        try:
            # USAJobs requires API key - placeholder for now
            logger.info("USAJobs API requires authentication - configure API key")
            # Implementation would go here with proper API key
        except Exception as e:
            logger.error(f"Error scraping USAJobs: {e}")
        
        return jobs
    
    def scrape_all_temp_jobs(self) -> List[Dict]:
        """Scrape all sources for low-skill/temp jobs"""
        all_jobs = []
        
        all_jobs.extend(self.scrape_remotive_entry_level())
        all_jobs.extend(self.scrape_snagajob_api())
        all_jobs.extend(self.scrape_usajobs_entry())
        
        # Remove duplicates
        unique_jobs = {job['url']: job for job in all_jobs if job.get('url')}.values()
        unique_jobs = list(unique_jobs)
        
        logger.info(f"Total unique low-skill/temp jobs: {len(unique_jobs)}")
        return unique_jobs


if __name__ == "__main__":
    # Test scrapers
    print("Testing Skill-Based Scraper...")
    skill_scraper = SkillBasedJobScraper()
    skill_jobs = skill_scraper.scrape_all_skills(['python', 'javascript'])
    print(f"Found {len(skill_jobs)} skill-based jobs")
    
    print("\nTesting Low-Skill/Temp Scraper...")
    temp_scraper = LowSkillTempJobScraper()
    temp_jobs = temp_scraper.scrape_all_temp_jobs()
    print(f"Found {len(temp_jobs)} temp jobs")
    
    if skill_jobs:
        print(f"\nSample skill job: {skill_jobs[0]['title']} at {skill_jobs[0]['company']}")
        print(f"Source URL: {skill_jobs[0]['source_url']}")
    
    if temp_jobs:
        print(f"\nSample temp job: {temp_jobs[0]['title']} at {temp_jobs[0]['company']}")
        print(f"Source URL: {temp_jobs[0]['source_url']}")
