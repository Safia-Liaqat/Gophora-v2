from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import json
import os
import re
import google.generativeai as genai
from pydantic import BaseModel, Field
import requests

from . import auth, models, schemas, context
from .database import SessionLocal, engine

# ADD THIS SNIPPET
from sqlalchemy import text

# Run the CREATE EXTENSION command before creating tables
with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    connection.commit()
# END OF SNIPPET

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === START: AI Configuration and Helpers ===

# Load API Key and Models from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    # Configure the Gemini client if an API key is provided
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not set — running without Gemini. Embedding/chat will fallback where possible.")

# Read model names and strip surrounding quotes if present (some .env files include quotes)
def _normalize_env(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return name.strip().strip('"').strip("'")

GEMINI_CHAT_MODEL_NAME = _normalize_env(os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash-latest"))
GEMINI_EMBED_MODEL_NAME = _normalize_env(os.getenv("GEMINI_EMBED_MODEL"))

# Function to generate embeddings for text
def generate_embedding(text: str) -> list[float] | None:
    """Generates a vector embedding for a given text using Gemini.

    Returns None on failure so callers can implement sensible fallbacks.
    """
    if not GEMINI_API_KEY or not GEMINI_EMBED_MODEL_NAME:
        # No model/key configured — bail out to allow tag-based fallback
        print("generate_embedding: GEMINI not configured (key/model missing)")
        return None
    try:
        # The client may raise; return None on any error so recommendation flow can fallback
        result = genai.embed_content(model=GEMINI_EMBED_MODEL_NAME, content=text)
        # result may be a dict or object depending on library version
        if isinstance(result, dict) and "embedding" in result:
            return result["embedding"]
        # Try attribute access as a fallback
        return getattr(result, "embedding", None)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def geocode_location(location: str) -> dict:
    if not location:
        return None
    
    api_key = os.getenv("GEOAPIFY_API_KEY")
    if not api_key:
        print("Warning: GEOAPIFY_API_KEY not set. Geocoding will not work.")
        return None

    try:
        response = requests.get(f"https://api.geoapify.com/v1/geocode/search?text={location}&apiKey={api_key}")
        response.raise_for_status()
        data = response.json()
        if data and data["features"]:
            # Geoapify returns lng, lat order
            lng, lat = data["features"][0]["geometry"]["coordinates"]
            return {"lat": lat, "lng": lng}
    except requests.RequestException as e:
        print(f"Geocoding error: {e}")
    return None


@app.post("/api/admin/re-geocode-opportunities")
def re_geocode_opportunities(db: Session = Depends(get_db)):
    """
    Finds all opportunities without lat/lng and attempts to geocode their location.
    This is useful for fixing old data.
    """
    # Find opportunities where coordinates are missing but a location string exists
    ops_to_fix = db.query(models.Opportunity).filter(
        models.Opportunity.lat == None,
        models.Opportunity.location != None
    ).all()
    
    updated_count = 0
    skipped_count = 0

    for opp in ops_to_fix:
        location_coords = geocode_location(opp.location)
        if location_coords:
            opp.lat = location_coords.get("lat")
            opp.lng = location_coords.get("lng")
            db.add(opp)
            updated_count += 1
        else:
            skipped_count += 1
            
    db.commit()
    
    return {
        "message": "Geocoding process completed.",
        "updated": updated_count,
        "skipped": skipped_count,
        "total_processed": len(ops_to_fix)
    }

# === END: AI Configuration and Helpers ===


@app.get("/api/debug/users", response_model=List[schemas.User])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.get("/api/debug/opportunities", response_model=List[schemas.Opportunity])
def get_all_opportunities(db: Session = Depends(get_db)):
    return db.query(models.Opportunity).all()



# In main.py

@app.post("/api/auth/register", response_model=schemas.User)
def register_user(user_data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    db_user = auth.get_user(db, email=user_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user_data.password)
    
    # --- START OF FIX ---
    
    # 1. Create the user object
    db_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(db_user)
    
    # 2. Commit the user to generate its ID
    # This is necessary before creating the profile which depends on the user's ID.
    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")

    # 3. Create the profile object with the now-valid user ID
    profile_data = {
        "country": user_data.country,
        "city": user_data.city,
    }
    if user_data.role == "seeker" and user_data.skills:
        profile_data["skills"] = [s.strip() for s in user_data.skills.split(',')]
    
    if user_data.role == "provider":
        profile_data["company_name"] = user_data.organizationName
        profile_data["company_website"] = user_data.website
    
    db_profile = models.Profile(user_id=db_user.id, **profile_data)
    db.add(db_profile)
    
    # 4. Commit the profile
    try:
        db.commit()
        db.refresh(db_user) # Refresh to load the full user object with its profile relationship
    except Exception as e:
        db.rollback()
        # Optionally, delete the user that was created in the first step to clean up
        db.delete(db_user)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error creating profile: {e}")
        
    # --- END OF FIX ---
    
    return db_user

@app.post("/api/auth/login", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = auth.get_user(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role != form_data.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are a {user.role} and cannot log in as a {form_data.role}",
        )
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/api/profiles/me", response_model=schemas.Profile)
def read_user_profile(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/api/profiles/me", response_model=schemas.Profile)
def update_user_profile(
    profile_update: schemas.ProfileBase,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()
    if not profile:
        profile = models.Profile(user_id=current_user.id, **profile_update.dict(exclude_unset=True))
        db.add(profile)
    else:
        update_data = profile_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile

@app.post("/api/opportunities", response_model=schemas.Opportunity)
def create_opportunity(
    opportunity: schemas.OpportunityCreate, # <-- CRITICAL FIX: Use OpportunityCreate
    current_user: models.User = Depends(auth.get_current_active_provider),
    db: Session = Depends(get_db),
):
    
    # Generate the embedding
    text_to_embed = f"Title: {opportunity.title}\nDescription: {opportunity.description}\nTags: {', '.join(opportunity.tags)}"
    embedding_vector = generate_embedding(text_to_embed)

    # Geocode the location
    location_coords = geocode_location(opportunity.location)
    lat = location_coords["lat"] if location_coords else None
    lng = location_coords["lng"] if location_coords else None

    # Create the new database model
    # The database will set created_at and updated_at automatically
    db_opportunity = models.Opportunity(
        title=opportunity.title,
        description=opportunity.description,
        type=opportunity.type,
        location=opportunity.location,
        lat=lat,
        lng=lng,
        tags=opportunity.tags,        # <-- Pass the list of tags directly
        provider_id=current_user.id,
        embedding=embedding_vector
        # Note: created_at and updated_at are set by default in the DB
    )
    
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity

# ... (all your other endpoints like apply, get applications, etc. remain the same)
@app.get("/api/applications/me", response_model=List[schemas.ApplicationWithOpportunity])
def read_seeker_applications(current_user: models.User = Depends(auth.get_current_active_seeker), db: Session = Depends(get_db)):
    return db.query(models.Application).filter(models.Application.seeker_id == current_user.id).options(joinedload(models.Application.opportunity)).all()

@app.post("/api/applications/apply", response_model=schemas.Application)
def apply_for_opportunity(opportunity_id: int, cover_letter: Optional[str] = None, current_user: models.User = Depends(auth.get_current_active_seeker), db: Session = Depends(get_db)):
    opportunity = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    existing_application = db.query(models.Application).filter(models.Application.seeker_id == current_user.id, models.Application.opportunity_id == opportunity_id).first()
    if existing_application:
        raise HTTPException(status_code=400, detail="Already applied to this opportunity")
    db_application = models.Application(seeker_id=current_user.id, opportunity_id=opportunity_id, cover_letter=cover_letter)
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

@app.get("/api/opportunities/me", response_model=List[schemas.Opportunity])
def read_provider_opportunities(current_user: models.User = Depends(auth.get_current_active_provider), db: Session = Depends(get_db)):
    return db.query(models.Opportunity).filter(models.Opportunity.provider_id == current_user.id).all()

@app.get("/api/opportunities", response_model=List[schemas.Opportunity])
def read_opportunities(db: Session = Depends(get_db)):
    return db.query(models.Opportunity).all()

@app.get("/api/opportunities/recommend", response_model=List[schemas.Opportunity])
def get_recommendations_for_seeker(
    current_user: models.User = Depends(auth.get_current_active_seeker),
    db: Session = Depends(get_db),
):
    # 1. Get Seeker's Profile and Skills
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()
    
    if not profile or not profile.skills:
        # If no profile or no skills, just return the 10 most recent jobs
        return db.query(models.Opportunity).order_by(models.Opportunity.created_at.desc()).limit(10).all()

    seeker_skills = profile.skills
    seeker_query = f"A job seeker with skills in: {', '.join(seeker_skills)}"

    # 2. Retrieve: Try semantic search via embeddings; if unavailable, fallback to tag overlap
    query_embedding = generate_embedding(seeker_query)
    similar_opportunities = []

    if query_embedding:
        try:
            # Get a larger list of candidates by semantic similarity
            similar_opportunities = db.query(models.Opportunity).join(models.Opportunity.provider).join(models.User.profile).filter(models.Profile.trust_score >= 40).order_by(
                models.Opportunity.embedding.cosine_distance(query_embedding)
            ).limit(20).all()
        except Exception as e:
            print(f"Error during semantic DB query: {e}")

    if not similar_opportunities:
        # Fallback: simple tag/skill overlap scoring
        seeker_set = set([s.lower() for s in seeker_skills])
        candidates = db.query(models.Opportunity).join(models.Opportunity.provider).join(models.User.profile).filter(models.Profile.trust_score >= 40).all()
        scored = []
        for opp in candidates:
            opp_tags = [t.lower() for t in (opp.tags or [])]
            overlap = len(seeker_set.intersection(opp_tags))
            if overlap > 0:
                scored.append((overlap, opp))
        # sort by overlap desc, then by created_at desc
        scored.sort(key=lambda x: (-x[0], getattr(x[1], 'created_at', None)), )
        similar_opportunities = [opp for score, opp in scored][:20]

    if not similar_opportunities:
        return [] # Return an empty list if no matches are found

    # 3. Filter: Use the AI to review the candidates and return ONLY IDs
    context = ""
    for opp in similar_opportunities:
        context += f"ID: {opp.id}\nTitle: {opp.title}\nDescription: {opp.description}\nTags: {', '.join(opp.tags)}\n---\n"

    filter_prompt = f"""
    You are a smart career assistant. A user has the following skills: "{seeker_query}"

    I have found 20 potential matches from the database. Your job is to:
    1.  Carefully review each job in the "Database Context" below.
    2.  Compare each job's title, description, and tags to the user's skills.
    3.  Create a new, filtered list containing ONLY the IDs of the jobs that are TRULY relevant.
    
    **CRITICAL RULE:** Only include jobs that are a strong match for the user's skills. Discard any that are not relevant.
    
    Finally, provide a response in the required JSON format.
    - The 'reply' field is not important for this, just put 'OK'.
    - The 'relevant_ids' list should contain ONLY the IDs of the relevant jobs you selected.
    - If NO jobs are relevant, return an empty 'relevant_ids' list.

    Database Context:
    {context}
    """
    
    try:
        filter_model = genai.GenerativeModel(
            GEMINI_CHAT_MODEL_NAME,
            generation_config={"response_mime_type": "application/json"}
        )
        ai_json_response = filter_model.generate_content(
            [filter_prompt],
            generation_config={"response_schema": AIFilterResponse}
        ).text
        
        ai_data = json.loads(ai_json_response)
        relevant_ids = ai_data.get("relevant_ids", [])

        # 4. Database Fetch: Use the safe IDs to get full, valid objects
        if not relevant_ids:
            return [] # Return empty list if AI filtered everything out

        final_opportunities = db.query(models.Opportunity).filter(
            models.Opportunity.id.in_(relevant_ids)
        ).all()
        
        return final_opportunities
        
    except Exception as e:
        print(f"Error in recommendation endpoint: {str(e)}")
        # Fallback: just return the 10 most recent jobs on error
        return db.query(models.Opportunity).order_by(models.Opportunity.created_at.desc()).limit(10).all()


@app.get("/api/opportunities/{opportunity_id}", response_model=schemas.Opportunity)
def read_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    db_opportunity = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if db_opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return db_opportunity

@app.put("/api/opportunities/{opportunity_id}", response_model=schemas.Opportunity)
def update_opportunity(opportunity_id: int, opportunity_update: schemas.OpportunityBase, current_user: models.User = Depends(auth.get_current_active_provider), db: Session = Depends(get_db)):
    db_opportunity = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if db_opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if db_opportunity.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this opportunity")
    update_data = opportunity_update.dict(exclude_unset=True)
    if "tags" in update_data and isinstance(update_data["tags"], str):
        update_data["tags"] = [tag.strip() for tag in update_data["tags"].split(",")] if update_data["tags"] else []
    for key, value in update_data.items():
        setattr(db_opportunity, key, value)
    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity

@app.delete("/api/opportunities/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(opportunity_id: int, current_user: models.User = Depends(auth.get_current_active_provider), db: Session = Depends(get_db)):
    db_opportunity = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if db_opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if db_opportunity.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this opportunity")
    db.delete(db_opportunity)
    db.commit()
    return

@app.get("/api/opportunities/{opportunity_id}/applications", response_model=List[schemas.Application])
def get_applications_for_opportunity(opportunity_id: int, current_user: models.User = Depends(auth.get_current_active_provider), db: Session = Depends(get_db)):
    opportunity = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id, models.Opportunity.provider_id == current_user.id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found or not owned by current provider")
    return db.query(models.Application).filter(models.Application.opportunity_id == opportunity_id).all()


# === NEW ENDPOINT: AI-Powered Recommendations ===
@app.post("/api/chat/recommend", response_model=schemas.ChatResponse)
def recommend_opportunities(chat_request: schemas.ChatRequest, db: Session = Depends(get_db)):
    # 1. Retrieve: Find relevant opportunities using vector search
    query_embedding = generate_embedding(chat_request.message)
    if not query_embedding:
        raise HTTPException(status_code=500, detail="Could not generate query embedding.")

    # Find the top 3 most relevant opportunities using cosine distance (<=>)
    similar_opportunities = db.query(models.Opportunity).order_by(
        models.Opportunity.embedding.cosine_distance(query_embedding)
    ).limit(3).all()

    if not similar_opportunities:
        return {"reply": "I couldn't find any opportunities in our database that match your request. Please try rephrasing your search."}

    # 2. Augment: Prepare a clean context for the AI model
    context = ""
    for opp in similar_opportunities:
        context += f"Opportunity Title: {opp.title}\n"
        context += f"Description: {opp.description}\n"
        context += f"Tags: {', '.join(opp.tags)}\n---\n"

    # 3. Generate: Use a restrictive prompt to ensure AI only uses the provided context
    prompt = f"""
    You are a career assistant for our platform, GOPHORA.
    Your ONLY job is to present the user with relevant opportunities from the database context provided below.

    **Strict Rules:**
    1. You MUST ONLY use the information from the "Database Context" section.
    2. Do NOT invent, add, or mention any opportunities not listed in the context.
    3. Introduce yourself and present the opportunities I found for the user based on their query: "{chat_request.message}"
    4. For each opportunity, briefly summarize it.

    **Database Context:**
    ---
    {context}
    ---
    """
    
    try:
        model = genai.GenerativeModel(GEMINI_CHAT_MODEL_NAME)
        response = model.generate_content(prompt)
        ai_reply = response.text
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating AI response: {str(e)}"
        )

    return {"reply": ai_reply}


class FilterOpportunity(BaseModel):
    """A single, relevant opportunity to show the user."""
    id: int = Field(description="The unique ID of the opportunity")
    title: str = Field(description="The job title")
    description: str = Field(description="A brief job description")
    location: Optional[str] = Field(description="The job location")
    type: Optional[str] = Field(description="The job type (e.g., 'job', 'internship')")
    tags: List[str] = Field(description="A list of relevant skills or tags")

class AIFilterResponse(BaseModel):
    """The AI's complete response, including an intro and a list of IDs."""
    reply: str = Field(description="A brief, one-sentence introduction (e.g., 'Here's what I found...')")
    relevant_ids: List[int] = Field(description="A list of opportunity IDs that are ACTUALLY relevant to the user's query. This can be an empty list if no matches are found.")

# --- END: Define the AI's JSON output structure ---


@app.post("/api/chat", response_model=schemas.ChatResponse)
def handle_chat(chat_request: schemas.ChatRequest, db: Session = Depends(get_db)):
    user_message = chat_request.message
    
    # 1. INTENT DETECTION (Same as before)
    intent_prompt = f"""
    Analyze the user's message and classify its intent.
    Respond with only one word: 'OPPORTUNITY' if the user is asking to find a job, role, or opportunity.
    Otherwise, respond with 'QUESTION'.

    User message: "{user_message}"
    """
    
    try:
        intent_model = genai.GenerativeModel(GEMINI_CHAT_MODEL_NAME)
        intent_response = intent_model.generate_content(intent_prompt)
        intent = intent_response.text.strip().upper()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting intent: {str(e)}")

    # 2. ACTION: Based on the intent
    
    # --- THIS IS THE NEW, ROBUST LOGIC ---
    if "OPPORTUNITY" in intent:
        # 1. Retrieve: Get top 10 potential matches
        query_embedding = generate_embedding(user_message)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Could not generate query embedding.")

        similar_opportunities = db.query(models.Opportunity).order_by(
            models.Opportunity.embedding.cosine_distance(query_embedding)
        ).limit(10).all()

        if not similar_opportunities:
            return {"reply": "I couldn't find any opportunities in our database that match your request. Please try rephrasing your search."}

        # 2. Filter: Use the AI to review the candidates and return ONLY IDs
        opportunity_context = ""
        for opp in similar_opportunities:
            # Provide all info for the AI to make a good decision
            opportunity_context += f"ID: {opp.id}\nTitle: {opp.title}\nDescription: {opp.description}\nTags: {', '.join(opp.tags)}\n---\n"

        filter_prompt = f"""
        You are a smart career assistant. A user is looking for a job.
        Their request is: "{user_message}"

        I have found 10 potential matches from the database. Your job is to:
        1.  Carefully review each job in the "Database Context" below.
        2.  Compare each job's title, description, and tags to the user's request.
        3.  Create a new, filtered list containing ONLY the IDs of the jobs that are TRULY relevant.
        
        **CRITICAL RULE:** If the user asks for 'C++' or 'Swift', you MUST DISCARD a job that only lists 'Python'. Only include exact or very close skill matches.
        
        Finally, provide a response in the required JSON format.
        - The 'reply' should be a single, friendly introduction.
        - The 'relevant_ids' list should contain ONLY the IDs of the relevant jobs you selected.
        - If NO jobs are relevant, return an empty 'relevant_ids' list and a 'reply' saying you couldn't find a match.

        Database Context:
        {opportunity_context}
        """
        
        try:
            filter_model = genai.GenerativeModel(
                GEMINI_CHAT_MODEL_NAME,
                generation_config={"response_mime_type": "application/json"}
            )
            ai_json_response = filter_model.generate_content(
                [filter_prompt],
                generation_config={"response_schema": AIFilterResponse}
            ).text
            
            ai_data = json.loads(ai_json_response)
            
            ai_reply = ai_data.get("reply", "Here's what I found:")
            relevant_ids = ai_data.get("relevant_ids", [])

            # 3. Database Fetch: Use the safe IDs to get full, valid objects
            final_opportunities = []
            if relevant_ids:
                final_opportunities = db.query(models.Opportunity).filter(
                    models.Opportunity.id.in_(relevant_ids)
                ).all()

            # This response is guaranteed to match your schemas.ChatResponse
            return {"reply": ai_reply, "opportunities": final_opportunities}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error filtering AI response: {str(e)}")

    # --- END OF NEW LOGIC ---

    # If the user is asking a general question, use the fixed context
    else: 
        general_qa_prompt = f"""
        You are GOPHORA AI, a helpful assistant. Answer the user's question using ONLY the provided context.
        ---CONTEXT---
        {context.WEBSITE_CONTEXT}
        ---END CONTEXT---
        User's Question: "{user_message}"
        Answer:
        """
        
        try:
            response_model = genai.GenerativeModel(GEMINI_CHAT_MODEL_NAME)
            final_response = response_model.generate_content(general_qa_prompt)
            ai_reply = final_response.text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating final AI response: {str(e)}")

        # Return with an empty list for opportunities
        return {"reply": ai_reply, "opportunities": []}
    
# Duplicate recommend endpoint removed. Kept the original `/api/opportunities/recommend`
# defined earlier in this file (placed before the dynamic `/api/opportunities/{opportunity_id}` route)

# In main.py, update your existing /api/verification/verify endpoint

@app.post("/api/verification/verify", response_model=schemas.VerificationResponse)
def verify_provider(
    request_data: schemas.VerificationRequest,
    current_user: models.User = Depends(auth.get_current_active_provider),
    db: Session = Depends(get_db)
):
    """
    Receives provider data, scrapes URL content, sends it to Gemini for analysis,
    and returns a Trust Score.
    """
    # 1. Scrape content from URLs to get more context
    scraped_content = ""
    if request_data.website_url:
        scraped_content += f"\n\n--- Scraped Content from Website ({request_data.website_url}) ---\n"
        scraped_content += scrape_url_content(request_data.website_url)

    if request_data.portfolio_url:
        scraped_content += f"\n\n--- Scraped Content from Portfolio ({request_data.portfolio_url}) ---\n"
        scraped_content += scrape_url_content(request_data.portfolio_url)

    if request_data.social_profiles:
        for profile in request_data.social_profiles:
            if profile.url:
                 scraped_content += f"\n\n--- Scraped Content from Social Profile ({profile.url}) ---\n"
                 scraped_content += scrape_url_content(profile.url)

    # 2. Prepare data and the NEW prompt for Gemini
    provider_data_json = request_data.model_dump_json(indent=2)

    prompt = f"""
    You are an expert digital verification analyst. Your task is to analyze the provider's legitimacy based on the JSON data and scraped web content below.

    **Provider Data (JSON):**
    {provider_data_json}

    **Scraped Web Content:**
    {scraped_content}

    **CRITICAL INSTRUCTION:** Your response MUST be a single, valid JSON object and NOTHING else. Do not include any text, explanations, or markdown formatting before or after the JSON object.

    **JSON Object Format:**
    {{
      "trust_score": <integer>,
      "reason": "<string>",
      "recommendation": "<'approve'|'review'|'reject'>"
    }}
    """

    try:
        # 3. Call Gemini API
        model = genai.GenerativeModel(GEMINI_CHAT_MODEL_NAME)
        response = model.generate_content(prompt)
        
        print(f"DEBUG: Gemini verification response: {response.text}")

        # Use regex to find the JSON block
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in the AI response.")
            
        json_string = json_match.group(0)
        ai_result = json.loads(json_string)

        trust_score = ai_result.get("trust_score", 0)
        recommendation = ai_result.get("recommendation", "review")

        profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()
        if profile:
            profile.trust_score = trust_score
            profile.verification_status = recommendation
            db.commit()

        return ai_result

    except Exception as e:
        print(f"Error during verification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get a valid response from the AI verification service: {str(e)}")


@app.get("/api/verification/status")
def get_verification_status(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Checks the current verification status of the logged-in user.
    """
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for this user.")

    return {
        "trust_score": profile.trust_score,
        "verification_status": profile.verification_status
    }

# ... (the rest of your main.py file, like /api/auth/register)
import requests
from bs4 import BeautifulSoup

def scrape_url_content(url: str) -> str:
    """
    Visits a URL, scrapes its text content, and returns a summary.
    This acts as our 'searching engine'.
    """
    if not url or not url.startswith(('http://', 'https://')):
        return "No valid URL provided."
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Return the first 500 characters for brevity
        return text[:500] + "..." if len(text) > 500 else text
    except requests.RequestException as e:
        return f"Could not access URL: {e}"
