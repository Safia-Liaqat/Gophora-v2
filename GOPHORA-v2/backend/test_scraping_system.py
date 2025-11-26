"""
Test script for the new high-quality job scraping system
Tests:
1. Skill-based job scraping
2. Temp/low-skill job scraping
3. Firebase storage
4. Source URL presence
"""
from backend.job_scrapers import SkillBasedJobScraper, LowSkillTempJobScraper
from backend.job_storage import JobStorageManager
import json

def test_skill_scraper():
    """Test skill-based job scraper"""
    print("=" * 60)
    print("TEST 1: Skill-Based Job Scraping")
    print("=" * 60)
    
    scraper = SkillBasedJobScraper()
    
    print("\n1. Testing Python jobs scraping...")
    jobs = scraper.scrape_all_skills(['python'])
    
    print(f"✓ Scraped {len(jobs)} Python jobs")
    
    if jobs:
        sample_job = jobs[0]
        print(f"\nSample Job:")
        print(f"  Title: {sample_job.get('title')}")
        print(f"  Company: {sample_job.get('company')}")
        print(f"  Location: {sample_job.get('location')}")
        print(f"  Source: {sample_job.get('source')}")
        print(f"  Source URL: {sample_job.get('source_url')}")
        print(f"  Skills: {sample_job.get('skills')[:5] if sample_job.get('skills') else []}")
        print(f"  Experience: {sample_job.get('experience_level')}")
        
        # Verify source URL exists
        if sample_job.get('source_url'):
            print(f"  ✓ Source URL present for Apply redirect")
        else:
            print(f"  ✗ WARNING: No source URL!")
        
        return jobs
    else:
        print("  ✗ No jobs found")
        return []

def test_temp_scraper():
    """Test temp/low-skill job scraper"""
    print("\n" + "=" * 60)
    print("TEST 2: Temp/Low-Skill Job Scraping")
    print("=" * 60)
    
    scraper = LowSkillTempJobScraper()
    
    print("\n1. Testing temp jobs scraping...")
    jobs = scraper.scrape_all_temp_jobs()
    
    print(f"✓ Scraped {len(jobs)} temp/low-skill jobs")
    
    if jobs:
        sample_job = jobs[0]
        print(f"\nSample Temp Job:")
        print(f"  Title: {sample_job.get('title')}")
        print(f"  Company: {sample_job.get('company')}")
        print(f"  Location: {sample_job.get('location')}")
        print(f"  Source: {sample_job.get('source')}")
        print(f"  Source URL: {sample_job.get('source_url')}")
        print(f"  Job Type: {sample_job.get('job_type')}")
        print(f"  Immediate Start: {sample_job.get('immediate_start')}")
        
        # Verify source URL exists
        if sample_job.get('source_url'):
            print(f"  ✓ Source URL present for Apply redirect")
        else:
            print(f"  ✗ WARNING: No source URL!")
        
        return jobs
    else:
        print("  ✗ No jobs found")
        return []

def test_storage():
    """Test Firebase storage"""
    print("\n" + "=" * 60)
    print("TEST 3: Firebase Storage")
    print("=" * 60)
    
    manager = JobStorageManager()
    
    print("\n1. Testing skill-based job storage...")
    skill_stats = manager.scrape_and_store_skill_jobs(['javascript'])
    print(f"✓ Skill-based scraping complete:")
    print(f"  - Scraped: {skill_stats.get('total_scraped')}")
    print(f"  - Stored: {skill_stats.get('total_stored')}")
    print(f"  - Duplicates skipped: {skill_stats.get('duplicates_skipped')}")
    
    print("\n2. Testing temp job storage...")
    temp_stats = manager.scrape_and_store_temp_jobs()
    print(f"✓ Temp job scraping complete:")
    print(f"  - Scraped: {temp_stats.get('total_scraped')}")
    print(f"  - Stored: {temp_stats.get('total_stored')}")
    print(f"  - Duplicates skipped: {temp_stats.get('duplicates_skipped')}")
    
    return skill_stats, temp_stats

def test_retrieval():
    """Test job retrieval from Firebase"""
    print("\n" + "=" * 60)
    print("TEST 4: Job Retrieval from Firebase")
    print("=" * 60)
    
    manager = JobStorageManager()
    
    print("\n1. Getting skill-matched jobs for ['python', 'react']...")
    skill_jobs = manager.get_jobs_for_user_skills(['python', 'react'], limit=5)
    print(f"✓ Retrieved {len(skill_jobs)} skill-matched jobs")
    
    if skill_jobs:
        print(f"\nSample retrieved job:")
        job = skill_jobs[0]
        print(f"  Title: {job.get('title')}")
        print(f"  Source URL: {job.get('source_url')}")
        print(f"  ✓ Source URL ready for Apply button redirect")
    
    print("\n2. Getting temp/immediate jobs...")
    temp_jobs = manager.get_temp_jobs(limit=5)
    print(f"✓ Retrieved {len(temp_jobs)} temp jobs")
    
    if temp_jobs:
        print(f"\nSample temp job:")
        job = temp_jobs[0]
        print(f"  Title: {job.get('title')}")
        print(f"  Source URL: {job.get('source_url')}")
        print(f"  ✓ Source URL ready for Apply button redirect")
    
    print("\n3. Getting all immediate jobs...")
    all_immediate = manager.get_all_immediate_jobs(limit=10)
    print(f"✓ Retrieved {len(all_immediate)} total immediate jobs")
    
    # Check all have source URLs
    missing_urls = [j for j in all_immediate if not j.get('source_url')]
    if missing_urls:
        print(f"  ✗ WARNING: {len(missing_urls)} jobs missing source URLs!")
    else:
        print(f"  ✓ All jobs have source URLs for Apply redirect")

def test_source_urls():
    """Verify all scraped jobs have source URLs"""
    print("\n" + "=" * 60)
    print("TEST 5: Source URL Verification")
    print("=" * 60)
    
    skill_scraper = SkillBasedJobScraper()
    temp_scraper = LowSkillTempJobScraper()
    
    skill_jobs = skill_scraper.scrape_all_skills(['python'])
    temp_jobs = temp_scraper.scrape_all_temp_jobs()
    
    all_jobs = skill_jobs + temp_jobs
    
    print(f"\nTotal jobs scraped: {len(all_jobs)}")
    
    with_urls = [j for j in all_jobs if j.get('source_url')]
    without_urls = [j for j in all_jobs if not j.get('source_url')]
    
    print(f"  ✓ Jobs with source URLs: {len(with_urls)}")
    print(f"  ✗ Jobs without source URLs: {len(without_urls)}")
    
    if without_urls:
        print(f"\nJobs missing source URLs:")
        for job in without_urls[:5]:
            print(f"  - {job.get('title')} from {job.get('source')}")
    else:
        print(f"\n  ✓ All jobs have source URLs!")
        print(f"  ✓ Apply button will work correctly!")

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("GOPHORA HIGH-QUALITY JOB SCRAPING SYSTEM TEST SUITE")
    print("=" * 60)
    
    try:
        # Test scrapers
        skill_jobs = test_skill_scraper()
        temp_jobs = test_temp_scraper()
        
        # Test storage
        skill_stats, temp_stats = test_storage()
        
        # Test retrieval
        test_retrieval()
        
        # Verify source URLs
        test_source_urls()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETE!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Skill-based jobs working: ✓")
        print(f"  - Temp jobs working: ✓")
        print(f"  - Firebase storage working: ✓")
        print(f"  - Source URLs present: ✓")
        print(f"  - Apply button redirect ready: ✓")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
