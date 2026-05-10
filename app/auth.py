import os
import hashlib
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Header, HTTPException

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "marksheet_extractor"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")  # Change in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database client
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]
users_collection = db["users"]
history_collection = db["history"]

# Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Utility Functions
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return user_email
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def verify_password(plain_password, hashed_password):
    try:
        password_sha256 = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return pwd_context.verify(password_sha256, hashed_password)
    except Exception:
        return False

def get_password_hash(password):
    try:
        password_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return pwd_context.hash(password_sha256)
    except Exception as e:
        raise e

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
