# GOPHORA AI Backend Documentation

## Overview
The GOPHORA AI backend uses **Firebase Firestore** for data storage, **LangChain** for AI orchestration, and **Google Gemini** for validation and embeddings. The system scrapes jobs from multiple sources, validates them using AI, and provides personalized recommendations.

## Architecture

### Components

1. **firebase_config.py** - Firebase/Firestore setup and helpers
2. **scrapers.py** - Web scraping from Indeed, Remote.co, Coursera, etc.
3. **ai_validation.py** - AI validation pipeline using LangChain + Gemini
4. **scheduler.py** - Background scraping every 30 minutes
5. **recommendation_engine.py** - Personalized job matching with embeddings
6. **models.py** - Pydantic models for data validation
7. **main.py** - FastAPI endpoints

### Firebase Collections

```
users/              - User accounts
profiles/           - User profiles with skills/interests
opportunities/      - User-posted opportunities
applications/       - Job applications
subscriptions/      - User subscriptions
scraped_jobs/       - Raw scraped data
verified_jobs/      - AI-validated jobs
immediate_jobs/     - Zero/low-skill jobs (same for all users)
skill_based_jobs/   - Skill-required jobs (personalized)
scraping_logs/      - Scraping activity logs
validation_logs/    - AI validation logs
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing
3. Enable Firestore Database
4. Enable Authentication (Email/Password)
5. Generate service account credentials:
   - Project Settings → Service Accounts
   - Generate new private key
   - Download JSON file as `firebase-credentials.json`
   - Place in backend directory

### 3. Get API Keys

#### Google Gemini API
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API key"
3. Copy your API key

#### Geoapify API (for geocoding)
1. Visit [Geoapify](https://www.geoapify.com/)
2. Create free account
3. Create project to get API key

#### OpenAI API (Optional - for cross-validation)
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create API key

### 4. Environment Variables

Create `.env` file in project root:

```env
# Security
SECRET_KEY=your_generated_secret_key_here

# Firebase (Option 1: Use credentials file)
FIREBASE_CREDENTIALS_PATH=backend/firebase-credentials.json

# Firebase (Option 2: Use environment variables)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com

# AI Models
GEMINI_API_KEY=your_gemini_api_key
GEMINI_EMBED_MODEL=models/text-embedding-004
GEMINI_CHAT_MODEL=gemini-1.5-flash

# Optional: OpenAI for cross-validation
OPENAI_API_KEY=your_openai_api_key

# Geoapify
GEOAPIFY_API_KEY=your_geoapify_api_key
VITE_GEOAPIFY_API_KEY=your_geoapify_api_key
```

### 5. Run the Backend

```bash
# From project root
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will:
- Start FastAPI server on http://localhost:8000
- Initialize Firebase connection
- Start background scraping scheduler (runs every 30 min)
- Immediately scrape and validate initial jobs

## AI Validation Pipeline

### How It Works

1. **Scraping** - Jobs scraped from multiple sources every 30 minutes
2. **Validation** - Each job is analyzed by AI for:
   - Legitimacy (scam detection)
   - Trust score (0-100)
   - Red flags identification
   - Content quality

3. **Categorization** - AI categorizes jobs into:
   - Primary category (Work, Education, Hobbies, Contribution)
   - Skill level (zero, low, medium, high)
   - Immediate availability (can start within 24-48 hours)
   - Payment timeframe

4. **Metadata Extraction** - AI extracts:
   - Required skills
   - Salary range
   - Experience level
   - Time commitment
   - Deadlines

5. **Embedding Generation** - Creates vector embeddings for semantic search

6. **Storage** - Approved jobs stored in:
   - `immediate_jobs` - Zero/low-skill, immediate start
   - `skill_based_jobs` - Requires specific skills
   - `verified_jobs` - All approved jobs

### Validation Criteria

Jobs are approved if:
- `is_legitimate == True`
- `trust_score >= 70`
- No critical red flags

## Job Recommendations

### Immediate Jobs (Zero-Effort)
- Available to ALL users
- No skills required
- Can start immediately
- Get paid within 24-48 hours
- Always promoted at top

### Skill-Based Jobs
- Personalized using user's profile
- Matched via semantic embeddings
- Requires specific skills
- Higher compensation
- Ranked by match score

## API Endpoints

### Jobs
```
GET  /api/jobs/immediate          - Get immediate jobs for all users
GET  /api/jobs/recommended        - Get personalized recommendations
GET  /api/jobs/category/{category} - Get jobs by category
GET  /api/jobs/search?q=query     - Semantic search
GET  /api/jobs/trending           - Get trending jobs
GET  /api/jobs/location/{loc}     - Get jobs by location
```

### Admin
```
GET  /api/admin/scraping-status   - Get scraper status
POST /api/admin/trigger-scrape    - Manually trigger scraping
GET  /api/admin/scraping-logs     - View scraping logs
```

## Monitoring

### Check Scraping Status
```python
from backend.scheduler import scraping_scheduler

status = scraping_scheduler.get_scheduler_status()
print(status)
```

### View Logs
Check Firestore `scraping_logs` collection for:
- Timestamp
- Total scraped
- Total validated
- Immediate jobs count
- Skill-based jobs count

## Customization

### Add New Job Source

Edit `backend/scrapers.py`:

```python
class NewSourceScraper(JobScraper):
    def scrape(self):
        # Implement scraping logic
        return jobs_list

# Add to orchestrator
class JobScraperOrchestrator:
    def __init__(self):
        self.scrapers = {
            # ...existing scrapers
            'new_source': NewSourceScraper()
        }
```

### Adjust Validation Thresholds

Edit `backend/ai_validation.py`:

```python
# Change approval threshold
full_result["approved"] = (
    validation_result["is_legitimate"] and 
    validation_result["trust_score"] >= 60  # Lower threshold
)
```

### Change Scraping Frequency

Edit `backend/scheduler.py`:

```python
# Change from 30 to 15 minutes
self.scheduler.add_job(
    func=self.scrape_and_validate_jobs,
    trigger=IntervalTrigger(minutes=15),  # Changed
    ...
)
```

## Troubleshooting

### Firebase Connection Issues
- Verify credentials file path
- Check Firebase project ID
- Ensure Firestore is enabled in Firebase Console

### Scraping Failures
- Check internet connection
- Some sites block scrapers (use proxies/APIs)
- Rate limiting may occur (adjust delays)

### AI Validation Errors
- Verify Gemini API key
- Check API quota/limits
- Ensure proper JSON format in prompts

### No Jobs Appearing
- Wait for first scraping cycle (30 min)
- Manually trigger: `POST /api/admin/trigger-scrape`
- Check scraping logs for errors

## Production Deployment

1. Use Firebase hosting or cloud functions
2. Set up proper environment variables
3. Enable Firebase security rules
4. Use job queues for scraping (Cloud Tasks)
5. Monitor API usage and costs
6. Implement caching for embeddings
7. Add error tracking (Sentry)

## Cost Optimization

- Cache embeddings to reduce API calls
- Batch validation requests
- Use Gemini Flash (cheaper) for most tasks
- Implement rate limiting
- Clean up old jobs regularly

## Security

- Never commit API keys or credentials
- Use Firebase security rules
- Implement proper authentication
- Validate all user inputs
- Rate limit API endpoints
- Monitor for abuse
