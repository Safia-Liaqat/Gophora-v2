"""
Pydantic Models/Schemas for Firebase Firestore
These models define the structure of documents stored in Firestore
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums for type safety
class UserRole(str, Enum):
    SEEKER = "seeker"
    PROVIDER = "provider"


class OpportunityStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    COMPLETED = "completed"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class SubscriptionPlan(str, Enum):
    EXPLORER = "Explorer"
    NAVIGATOR = "Navigator"
    COMMANDER = "Commander"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class SkillLevel(str, Enum):
    ZERO = "zero"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class JobCategory(str, Enum):
    WORK = "Work"
    EDUCATION = "Education"
    HOBBIES = "Hobbies"
    CONTRIBUTION = "Contribution"


# User Models
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


# Profile Models
class ProfileBase(BaseModel):
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    trust_score: int = 0
    verification_status: str = "unverified"


class ProfileCreate(ProfileBase):
    user_id: str


class Profile(ProfileBase):
    id: Optional[str] = None
    user_id: str
    
    class Config:
        from_attributes = True


# Opportunity Models
class OpportunityBase(BaseModel):
    title: str
    description: str
    type: Optional[str] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    status: OpportunityStatus = OpportunityStatus.OPEN


class OpportunityCreate(OpportunityBase):
    provider_id: str


class Opportunity(OpportunityBase):
    id: Optional[str] = None
    provider_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    embedding: Optional[List[float]] = None
    
    class Config:
        from_attributes = True


# Scraped Job Models (AI-enhanced)
class ScrapedJobBase(BaseModel):
    title: str
    company: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    source: str
    location: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ValidatedJob(ScrapedJobBase):
    id: Optional[str] = None
    # Validation fields
    is_legitimate: bool = False
    trust_score: int = 0
    confidence: float = 0.0
    red_flags: List[str] = Field(default_factory=list)
    approved: bool = False
    
    # Categorization fields
    primary_category: Optional[JobCategory] = None
    subcategory: Optional[str] = None
    skill_level: Optional[SkillLevel] = None
    is_immediate: bool = False
    payment_timeframe: Optional[str] = None
    
    # Metadata fields
    required_skills: List[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    time_commitment: Optional[str] = None
    deadline: Optional[str] = None
    
    # Embedding for semantic search
    embedding: Optional[List[float]] = None
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


# Application Models
class ApplicationBase(BaseModel):
    cover_letter: Optional[str] = None
    status: ApplicationStatus = ApplicationStatus.PENDING


class ApplicationCreate(ApplicationBase):
    seeker_id: str
    opportunity_id: str


class Application(ApplicationBase):
    id: Optional[str] = None
    seeker_id: str
    opportunity_id: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


# Subscription Models
class SubscriptionBase(BaseModel):
    plan_name: SubscriptionPlan
    status: SubscriptionStatus


class SubscriptionCreate(SubscriptionBase):
    user_id: str
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None


class Subscription(SubscriptionBase):
    id: Optional[str] = None
    user_id: str
    start_date: datetime
    end_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True