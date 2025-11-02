"""
This file handles the database connection and session management for the application.
It sets up the SQLAlchemy engine and provides a session factory for interacting
with the database.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from a .env file (especially for local development)
load_dotenv()

# The connection string for the database, loaded from environment variables.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# The main entry point for SQLAlchemy to communicate with the database.
# The logic here handles different connection arguments for SQLite vs. PostgreSQL.
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# A factory for creating new database sessions.
# Each instance of SessionLocal will be a new database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# A base class for our declarative models (like User in models.py).
# The models will inherit from this class.
Base = declarative_base()
