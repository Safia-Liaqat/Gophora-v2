"""
Safia:
SQLAlchemy Models: Write Python code for all database models (User, Profile, Opportunity, Application, Subscription)
in models.py based on the provided SQL schema.

Database Creation: Use SQLAlchemy's engine to create all tables in your local PostgreSQL database.

This file defines the database models for the application using SQLAlchemy's ORM.
Each class in this file corresponds to a table in the database.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from .database import Base
from pgvector.sqlalchemy import Vector

# Represents the 'users' table in the database.
# SQLAlchemy's ORM maps this class to the table, and its attributes to the columns.
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, nullable=False) # CHECK (role IN ('seeker', 'provider'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships:
    profile = relationship("Profile", back_populates="user", uselist=False)
    opportunities = relationship("Opportunity", back_populates="provider")
    applications = relationship("Application", back_populates="seeker")
    subscription = relationship("Subscription", back_populates="user", uselist=False)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    avatar_url = Column(Text)
    bio = Column(Text)
    skills = Column(ARRAY(Text))
    interests = Column(ARRAY(Text))
    company_name = Column(String)
    company_website = Column(Text)
    country = Column(String)
    city = Column(String)
    trust_score = Column(Integer)
    verification_status = Column(String)
    user = relationship("User", back_populates="profile")

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    type = Column(String)
    location = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    tags = Column(ARRAY(Text))
    status = Column(String, default="open") # CHECK (status IN ('open', 'closed', 'completed'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    provider = relationship("User", back_populates="opportunities")
    applications = relationship("Application", back_populates="opportunity")
    embedding = Column(Vector(768), nullable=True)

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending") # CHECK (status IN ('pending', 'accepted', 'rejected'))
    cover_letter = Column(Text)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    seeker = relationship("User", back_populates="applications")
    opportunity = relationship("Opportunity", back_populates="applications")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan_name = Column(String, nullable=False) # CHECK (plan_name IN ('Explorer', 'Navigator', 'Commander'))
    status = Column(String, nullable=False) # CHECK (status IN ('active', 'canceled', 'past_due'))
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    user = relationship("User", back_populates="subscription")