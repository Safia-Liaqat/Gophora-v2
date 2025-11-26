# 🚀 GOPHORA Backend

## Overview
AI-powered job scraping, validation, and personalized recommendation system built with FastAPI, Firebase, and LangChain.

## 📁 Directory Structure

```
backend/
├── app.py                      # ✨ Main FastAPI application (START HERE)
├── __init__.py                 # Package initialization
│
├── Core Services/
│   ├── firebase_config.py      # Firebase/Firestore setup & helpers
│   ├── auth.py                 # Authentication (JWT, password hashing)
│   ├── config.py               # Configuration settings
│   └── models.py               # Pydantic data models
│
├── AI & Scraping/
│   ├── scrapers.py             # Web scraping from 9+ job sources
│   ├── ai_validation.py        # LangChain AI validation pipeline
│   ├── recommendation_engine.py # Personalized job matching
│   └── scheduler.py            # Background scraping (every 30 min)
│
├── Legacy Files/
│   ├── main.py                 # Old PostgreSQL version (deprecated)
│   ├── main_new.py             # Previous version (use app.py instead)
│   ├── main_test.py            # Test version
│   ├── database.py             # Old SQLAlchemy setup (deprecated)
│   ├── schemas.py              # Old schemas (deprecated)
│   └── context.py              # Old context helper (deprecated)
│
└── Documentation/
    ├── AI_README.md            # Detailed AI system documentation
    ├── requirements.txt        # Python dependencies
    └── Dockerfile              # Docker configuration (optional)
```

## 🎯 Key Files

### **app.py** - Main Application ⭐
The main FastAPI application with all endpoints. Start here!

**Features:**
- 🔐 User authentication (register/login)
- 🎯 Immediate jobs (zero-skill, for all users)
- 🤖 Personalized recommendations (AI-matched)
- 🔍 Semantic search
- 📊 Admin dashboard & stats
- 🧪 Firebase testing endpoint

### **firebase_config.py** - Database
- Firebase Admin SDK initialization
- Firestore helper functions
- Collection management

### **scrapers.py** - Job Collection
- Indeed, Remote.co, Coursera, LinkedIn, Upwork
- 9+ job sources
- Rate limiting & error handling

### **ai_validation.py** - AI Pipeline
- LangChain integration
- Scam detection
- Trust scoring (0-100)
- Job categorization
- Metadata extraction
- Embedding generation

### **recommendation_engine.py** - Matching
- Cosine similarity
- Immediate jobs filtering
- Skill-based matching
- Semantic search
- Trending jobs

### **scheduler.py** - Automation
- APScheduler background tasks
- Scrapes every 30 minutes
- Automatic validation
- Data cleanup

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` in project root:

```env
SECRET_KEY=your_secret_key
FIREBASE_CREDENTIALS_PATH=backend/firebase-credentials.json
GEMINI_API_KEY=your_gemini_key
GEOAPIFY_API_KEY=your_geoapify_key
```

### 3. Run the Backend

```bash
# From project root (GOPHORA-v2/)
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Or use the run script:

```bash
python run.py
```

### 4. Access API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Immediate Jobs**: http://localhost:8000/api/jobs/immediate

## 📊 API Endpoints

### Authentication
```
POST /api/auth/register     - Register new user
POST /api/auth/login        - Login user
```

### Jobs - Immediate (Zero-Skill)
```
GET /api/jobs/immediate     - Jobs for everyone (no skills needed)
```

### Jobs - Personalized
```
GET /api/jobs/recommended/{user_id}  - Personalized recommendations
GET /api/jobs/skill-based/{user_id}  - Skill-matched jobs
```

### Jobs - Search & Filter
```
GET /api/jobs/search?q=query         - Semantic AI search
GET /api/jobs/category/{category}    - Filter by category
GET /api/jobs/location/{location}    - Filter by location
GET /api/jobs/trending               - Trending jobs
```

### User Profile
```
GET /api/users/{user_id}/profile     - Get profile
PUT /api/users/{user_id}/profile     - Update profile
```

### Applications
```
POST /api/applications               - Submit application
GET  /api/applications/user/{id}     - Get user's applications
```

### Admin
```
GET  /api/admin/scraping-status      - Scheduler status
POST /api/admin/trigger-scrape       - Manual scrape
GET  /api/admin/scraping-logs        - View logs
GET  /api/admin/stats                - System statistics
```

### Testing
```
GET /                                - Health check
GET /health                          - Detailed health
GET /test-firebase                   - Test Firebase
```

## 🔧 Configuration

### Firestore Collections

```
users/              - User accounts
profiles/           - User profiles (skills, interests)
scraped_jobs/       - Raw scraped data
verified_jobs/      - AI-validated jobs
immediate_jobs/     - Zero-skill jobs
skill_based_jobs/   - Skill-required jobs
applications/       - Job applications
scraping_logs/      - Activity logs
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT secret key | ✅ Yes |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase JSON | ✅ Yes |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ Yes |
| `GEOAPIFY_API_KEY` | Geoapify API key | ✅ Yes |
| `OPENAI_API_KEY` | OpenAI key (optional) | ❌ No |

## 🤖 AI Features

### 1. Automated Scraping
- Runs every 30 minutes
- Scrapes from 9+ sources
- Stores in Firestore

### 2. AI Validation
Every job is validated for:
- ✅ Legitimacy (scam detection)
- 📊 Trust score (0-100)
- 🚩 Red flags
- 📁 Category (Work/Education/Hobbies/Contribution)
- 🎯 Skill level (zero/low/medium/high)
- 💰 Salary, skills, location extraction

### 3. Personalization
- 768-dimension embeddings
- Cosine similarity matching
- User skill matching
- Semantic search

## 📝 Development

### File Naming Convention

- `app.py` - Main application (production)
- `*_test.py` - Test versions
- `main*.py` - Legacy/deprecated versions

### Adding New Features

1. Add endpoint to `app.py`
2. Update models in `models.py` if needed
3. Test with `/docs` interactive API

### Adding New Job Sources

Edit `scrapers.py`:

```python
class NewSourceScraper(JobScraper):
    def scrape(self):
        # Your scraping logic
        return jobs
```

Add to orchestrator:

```python
self.scrapers['new_source'] = NewSourceScraper()
```

## 🐛 Troubleshooting

### Firebase Connection Error
```bash
# Check credentials file exists
ls backend/firebase-credentials.json

# Verify .env configuration
cat .env | grep FIREBASE
```

### Import Errors
```bash
# Ensure all dependencies installed
pip install -r backend/requirements.txt

# Run from correct directory
cd GOPHORA-v2/
python -m uvicorn backend.app:app --reload
```

### Scraper Not Running
The scheduler starts automatically. To manually trigger:

```bash
curl -X POST http://localhost:8000/api/admin/trigger-scrape
```

## 📚 Additional Documentation

- **AI System**: See `AI_README.md`
- **Setup Guide**: See `../SETUP_GUIDE.md`
- **Implementation**: See `../IMPLEMENTATION_SUMMARY.md`

## 🎯 Production Deployment

1. Set `reload=False` in uvicorn
2. Use production ASGI server (Gunicorn)
3. Set up Firebase security rules
4. Enable HTTPS
5. Configure rate limiting
6. Set up monitoring (Sentry)

## 🤝 Contributing

1. Keep `app.py` as the main entry point
2. Follow existing code structure
3. Add docstrings to all functions
4. Test with `/test-firebase` endpoint
5. Check `/health` before committing

## 📄 License

See LICENSE file in project root.

---

**Made with ❤️ by the GOPHORA Team**
