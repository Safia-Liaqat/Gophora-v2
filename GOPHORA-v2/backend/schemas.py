"""
Safia:
Pydantic Schemas: Create schemas.py and define Pydantic models for API data validation
(e.g., UserCreate, UserLogin, OpportunityCreate, ProfileBase, ProfileCreate, etc.)
for all models (User, Profile, Opportunity, Application, Subscription).

This file defines the Pydantic models (schemas) for the application.
These schemas are used by FastAPI for data validation, serialization, and documentation.
They define the shape of the data for API requests and responses, and are separate
from the SQLAlchemy database models.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# A base schema for a User, containing common attributes.
# Other schemas inherit from this to avoid repetition.
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str

# A schema used specifically for creating a new user.
# It inherits the email from UserBase and adds a password.
class UserCreate(UserBase):
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: str
    country: Optional[str] = None
    city: Optional[str] = None
    skills: Optional[str] = None
    organizationName: Optional[str] = None
    website: Optional[str] = None

# A schema used for reading/returning user data from the API.
# It includes attributes that are safe to expose publicly (no password).
class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        # This allows the Pydantic model to read data from ORM models (like SQLAlchemy).
        from_attributes = True

# Schema for the response when a user successfully logs in.
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for the data encoded within a JWT access token.
class TokenData(BaseModel):
    email: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

class ProfileBase(BaseModel):
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

class ProfileCreate(ProfileBase):
    user_id: int

class Profile(ProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# 1. This is your existing OpportunityBase (or similar)
#    It's good for reading data, but not for creating.
class OpportunityBase(BaseModel):
    title: str
    description: str
    type: Optional[str] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

# --- UPDATE THIS SCHEMA ---
# This is the correct schema for creating a new opportunity.
# It only includes fields the user provides.
class OpportunityCreate(OpportunityBase):
    tags: List[str] = []  # <-- Changed from str to List[str] to match your form

# This is your main schema for *returning* data (reading from the DB)
class Opportunity(OpportunityBase):
    id: int
    provider_id: int
    created_at: datetime
    updated_at: datetime  # <-- You will need to add this to your model
    tags: List[str] = []
    status: Optional[str] = None

    class Config:
        from_attributes = True # Use this instead of orm_mode for Pydantic V2

class ApplicationBase(BaseModel):
    status: Optional[str] = "pending"
    cover_letter: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    seeker_id: int
    opportunity_id: int

class Application(ApplicationBase):
    id: int
    seeker_id: int
    opportunity_id: int
    submitted_at: datetime

    class Config:
        from_attributes = True

class ApplicationWithOpportunity(Application):
    opportunity: Opportunity

class SubscriptionBase(BaseModel):
    plan_name: str
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class SubscriptionCreate(SubscriptionBase):
    user_id: int

class Subscription(SubscriptionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    opportunities: Optional[List[Opportunity]] = None

class SocialProfile(BaseModel):
    platform: str
    url: str

class VerificationRequest(BaseModel):
    provider_type: str
    provider_name: str
    email: str
    website_url: Optional[str] = None
    domain_age: Optional[int] = None
    social_profiles: Optional[List[SocialProfile]] = None
    portfolio_url: Optional[str] = None
    video_intro_url: Optional[str] = None
    user_description: Optional[str] = None

class VerificationResponse(BaseModel):
    trust_score: int
    reason: str
    recommendation: str