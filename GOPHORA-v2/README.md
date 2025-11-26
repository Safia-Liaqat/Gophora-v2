# GOPHORA

GOPHORA is an intelligent job search platform that connects job seekers with opportunities worldwide. The platform features AI-powered chatbot assistance using Google Gemini, automated job scraping from multiple sources, and personalized job recommendations. Built with React frontend and FastAPI backend, it provides real-time job updates and smart filtering capabilities.

## How to Run

### Prerequisites
- Node.js (v18 or later)
- Python 3.8+
- Firebase account
- Google Gemini API key

### Steps

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd GOPHORA-v2
```

2. **Set up environment variables**
```bash
cp .env.example .env
```
Edit `.env` file and add:
- `SECRET_KEY`: Generate using `openssl rand -hex 32`
- `GEMINI_API_KEY`: Get from https://aistudio.google.com/apikey
- `GEOAPIFY_API_KEY`: Get from https://www.geoapify.com/
- `FIREBASE_CREDENTIALS_PATH`: Add your Firebase credentials JSON file to `backend/` folder

3. **Install dependencies**
```bash
# Frontend
npm install

# Backend
pip install -r backend/requirements.txt
```

4. **Run the application**
```bash
# Terminal 1 - Start backend
python -m backend.scraping_app

# Terminal 2 - Start frontend
npm run dev
```

5. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

Run the three commands above before starting the frontend (`npm run dev`) if you want the backend to be restarted with a fresh database.