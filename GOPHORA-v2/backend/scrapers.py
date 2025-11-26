"""
Web Scraping Module for Multiple Job Sources
Scrapes opportunities from various platforms 24/7
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import logging
from typing import List, Dict, Optional
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobScraper:
    """Base class for job scraping"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()
    
    def extract_salary(self, text: str) -> Optional[str]:
        """Extract salary information from text"""
        salary_patterns = [
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*-\s*\$\d+(?:,\d{3})*(?:\.\d{2})?)?',
            r'\d+(?:,\d{3})*\s*(?:USD|EUR|GBP)',
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None


class IndeedScraper(JobScraper):
    """Scraper for Indeed job listings"""
    
    def scrape(self, keywords: str = "remote job", location: str = "", max_pages: int = 3) -> List[Dict]:
        """Scrape Indeed for job listings"""
        jobs = []
        base_url = "https://www.indeed.com/jobs"
        
        for page in range(max_pages):
            try:
                params = {
                    'q': keywords,
                    'l': location,
                    'start': page * 10
                }
                
                response = requests.get(base_url, params=params, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_cards = soup.find_all('div', class_=re.compile('job_seen_beacon'))
                
                for card in job_cards:
                    try:
                        title_elem = card.find('h2', class_='jobTitle')
                        title = self.clean_text(title_elem.get_text()) if title_elem else None
                        
                        company_elem = card.find('span', class_='companyName')
                        company = self.clean_text(company_elem.get_text()) if company_elem else None
                        
                        location_elem = card.find('div', class_='companyLocation')
                        job_location = self.clean_text(location_elem.get_text()) if location_elem else None
                        
                        snippet_elem = card.find('div', class_='job-snippet')
                        description = self.clean_text(snippet_elem.get_text()) if snippet_elem else None
                        
                        link_elem = title_elem.find('a') if title_elem else None
                        job_url = f"https://www.indeed.com{link_elem.get('href')}" if link_elem and link_elem.get('href') else None
                        
                        if title and company:
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': job_location,
                                'description': description,
                                'url': job_url,
                                'source': 'Indeed',
                                'scraped_at': datetime.utcnow().isoformat(),
                                'raw_data': str(card)[:500]  # Store partial HTML for validation
                            })
                    except Exception as e:
                        logger.error(f"Error parsing Indeed job card: {e}")
                        continue
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error scraping Indeed page {page}: {e}")
                continue
        
        logger.info(f"Scraped {len(jobs)} jobs from Indeed")
        return jobs


class LinkedInScraper(JobScraper):
    """Scraper for LinkedIn job listings (requires authentication or API)"""
    
    def scrape(self, keywords: str = "remote", max_results: int = 50) -> List[Dict]:
        """
        Scrape LinkedIn jobs (Note: LinkedIn has anti-scraping measures)
        For production, use LinkedIn API or consider alternative approaches
        """
        jobs = []
        base_url = "https://www.linkedin.com/jobs/search"
        
        try:
            params = {
                'keywords': keywords,
                'location': 'Worldwide',
                'f_WT': '2'  # Remote filter
            }
            
            # Note: LinkedIn requires authentication and has strict anti-scraping
            # This is a simplified example - use LinkedIn API for production
            logger.warning("LinkedIn scraping requires proper authentication. Consider using LinkedIn API.")
            
            # Placeholder for LinkedIn API integration
            # You would use linkedin-api library here
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
        
        return jobs


class RemoteCoScraper(JobScraper):
    """Scraper for Remote.co job listings"""
    
    def scrape(self, category: str = "", max_pages: int = 3) -> List[Dict]:
        """Scrape Remote.co for remote job listings"""
        jobs = []
        base_url = "https://remote.co/remote-jobs"
        
        try:
            response = requests.get(base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_listings = soup.find_all('div', class_=re.compile('job_listing'))
            
            for listing in job_listings[:max_pages * 10]:
                try:
                    title_elem = listing.find('span', class_='title')
                    title = self.clean_text(title_elem.get_text()) if title_elem else None
                    
                    company_elem = listing.find('span', class_='company')
                    company = self.clean_text(company_elem.get_text()) if company_elem else None
                    
                    category_elem = listing.find('span', class_='category')
                    job_category = self.clean_text(category_elem.get_text()) if category_elem else None
                    
                    link_elem = listing.find('a')
                    job_url = link_elem.get('href') if link_elem else None
                    
                    if title and company:
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': 'Remote',
                            'category': job_category,
                            'url': job_url,
                            'source': 'Remote.co',
                            'scraped_at': datetime.utcnow().isoformat()
                        })
                except Exception as e:
                    logger.error(f"Error parsing Remote.co listing: {e}")
                    continue
            
            logger.info(f"Scraped {len(jobs)} jobs from Remote.co")
            
        except Exception as e:
            logger.error(f"Error scraping Remote.co: {e}")
        
        return jobs


class UpworkScraper(JobScraper):
    """Scraper for Upwork freelance opportunities (requires API)"""
    
    def scrape(self, skills: List[str] = None, max_results: int = 50) -> List[Dict]:
        """
        Scrape Upwork jobs (requires Upwork API access)
        """
        jobs = []
        
        try:
            # Upwork requires OAuth authentication
            # Use Upwork API for production
            logger.warning("Upwork scraping requires API access. Please use Upwork API.")
            
            # Placeholder for Upwork API integration
            
        except Exception as e:
            logger.error(f"Error scraping Upwork: {e}")
        
        return jobs


class EventbriteScraper(JobScraper):
    """Scraper for Eventbrite volunteer opportunities"""
    
    def scrape(self, keywords: str = "volunteer", location: str = "", max_results: int = 50) -> List[Dict]:
        """Scrape Eventbrite for volunteer events"""
        jobs = []
        
        try:
            # Eventbrite API is recommended for production use
            api_url = "https://www.eventbriteapi.com/v3/events/search/"
            
            # Placeholder - requires Eventbrite API token
            logger.warning("Eventbrite scraping requires API token. Use Eventbrite API.")
            
        except Exception as e:
            logger.error(f"Error scraping Eventbrite: {e}")
        
        return jobs


class GigPlatformScraper(JobScraper):
    """Scraper for gig economy platforms (TaskRabbit, Fiverr, etc.)"""
    
    def scrape_taskrabbit(self, location: str = "") -> List[Dict]:
        """Scrape TaskRabbit for immediate gig opportunities"""
        jobs = []
        
        try:
            # TaskRabbit doesn't have a public API
            # Web scraping may violate ToS - use with caution
            logger.warning("TaskRabbit scraping may violate ToS. Consider partnerships or API access.")
            
        except Exception as e:
            logger.error(f"Error scraping TaskRabbit: {e}")
        
        return jobs


class CourseraScraper(JobScraper):
    """Scraper for Coursera volunteer/teaching opportunities"""
    
    def scrape(self, category: str = "", max_results: int = 20) -> List[Dict]:
        """Scrape Coursera for opportunities"""
        jobs = []
        base_url = "https://www.coursera.org/about/careers"
        
        try:
            response = requests.get(base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Coursera career page structure (adjust selectors as needed)
            job_elements = soup.find_all('a', href=re.compile('/about/careers/jobs'))
            
            for elem in job_elements[:max_results]:
                try:
                    title = self.clean_text(elem.get_text())
                    url = f"https://www.coursera.org{elem.get('href')}"
                    
                    if title:
                        jobs.append({
                            'title': title,
                            'company': 'Coursera',
                            'location': 'Remote',
                            'url': url,
                            'source': 'Coursera',
                            'category': 'Education',
                            'scraped_at': datetime.utcnow().isoformat()
                        })
                except Exception as e:
                    logger.error(f"Error parsing Coursera job: {e}")
                    continue
            
            logger.info(f"Scraped {len(jobs)} opportunities from Coursera")
            
        except Exception as e:
            logger.error(f"Error scraping Coursera: {e}")
        
        return jobs


class JobScraperOrchestrator:
    """Orchestrates scraping from multiple sources"""
    
    def __init__(self):
        self.scrapers = {
            'indeed': IndeedScraper(),
            'linkedin': LinkedInScraper(),
            'remote_co': RemoteCoScraper(),
            'upwork': UpworkScraper(),
            'eventbrite': EventbriteScraper(),
            'coursera': CourseraScraper(),
            'gig_platforms': GigPlatformScraper()
        }
    
    def scrape_all(self, keywords: str = "remote job", focus_immediate: bool = True) -> Dict[str, List[Dict]]:
        """Scrape from all sources"""
        all_jobs = {}
        
        logger.info("Starting comprehensive job scraping...")
        
        # Scrape Indeed
        try:
            if focus_immediate:
                # Focus on immediate/hourly jobs
                immediate_keywords = ["hourly", "immediate start", "no experience", "entry level"]
                all_jobs['indeed'] = self.scrapers['indeed'].scrape(keywords=" OR ".join(immediate_keywords))
            else:
                all_jobs['indeed'] = self.scrapers['indeed'].scrape(keywords=keywords)
        except Exception as e:
            logger.error(f"Indeed scraping failed: {e}")
            all_jobs['indeed'] = []
        
        # Scrape Remote.co
        try:
            all_jobs['remote_co'] = self.scrapers['remote_co'].scrape()
        except Exception as e:
            logger.error(f"Remote.co scraping failed: {e}")
            all_jobs['remote_co'] = []
        
        # Scrape Coursera
        try:
            all_jobs['coursera'] = self.scrapers['coursera'].scrape()
        except Exception as e:
            logger.error(f"Coursera scraping failed: {e}")
            all_jobs['coursera'] = []
        
        # Add more scrapers as needed
        
        total_jobs = sum(len(jobs) for jobs in all_jobs.values())
        logger.info(f"Total jobs scraped: {total_jobs}")
        
        return all_jobs
    
    def scrape_immediate_jobs(self) -> List[Dict]:
        """Scrape specifically for immediate, zero-skill jobs"""
        immediate_jobs = []
        
        # Keywords for zero/low-skill immediate jobs
        keywords = [
            "no experience required",
            "immediate start",
            "hourly pay",
            "same day pay",
            "entry level",
            "beginner friendly",
            "training provided",
            "flexible hours"
        ]
        
        for keyword in keywords:
            try:
                jobs = self.scrapers['indeed'].scrape(keywords=keyword, max_pages=2)
                immediate_jobs.extend(jobs)
                time.sleep(3)  # Rate limiting
            except Exception as e:
                logger.error(f"Error scraping for keyword '{keyword}': {e}")
        
        return immediate_jobs
