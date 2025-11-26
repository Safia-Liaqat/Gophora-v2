from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from . import models
from .firebase_config import FirestoreHelper, FirestoreCollections
from .config import SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)  # 24 hours default
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_firestore():
    """Get Firestore helper instance"""
    return FirestoreHelper()

def get_user_by_email(email: str):
    """Get user from Firestore by email"""
    firestore = get_firestore()
    users = firestore.query_documents(
        FirestoreCollections.USERS,
        [("email", "==", email)]
    )
    return users[0] if users else None

def get_user_by_id(user_id: str):
    """Get user from Firestore by ID"""
    firestore = get_firestore()
    return firestore.get_document(FirestoreCollections.USERS, user_id)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_seeker(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "seeker":
        raise HTTPException(status_code=403, detail="Not authorized: Requires seeker role")
    return current_user

def get_current_active_provider(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "provider":
        raise HTTPException(status_code=403, detail="Not a provider")
    return current_user
