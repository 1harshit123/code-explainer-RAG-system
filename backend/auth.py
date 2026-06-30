import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from pwdlib import PasswordHash
from dotenv import load_dotenv
from fastapi import Depends, Header
from sqlmodel import Session, select, or_
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from google.oauth2 import id_token
from google.auth.transport import requests
import httpx


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID")

print(f"JWT_secret: {JWT_SECRET_KEY}")
print(f"ALGORITHM: {ALGORITHM}")
print(f"GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID}")
load_dotenv(override=True)

from model import User 
from database import engine 

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()



def verify_google_token(token: str) -> dict | None:
    """Verifies the Google Access Token by querying Google's tokeninfo endpoint."""
    try:
        response = httpx.get(
            f"https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

def get_or_create_google_user(session: Session, user_info: dict) -> User:
    """Finds an existing user by email or creates a new one."""
    email = user_info.get("email")
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    
    if not user:
        user = User(
            email=email,
            username=user_info.get("name"),       
            profile_pic=user_info.get("picture")  
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
    return user

class RegisterPayload(BaseModel):
    emailOrUsername: str
    email: str
    password: str
    confirmPassword: str

class LoginPayload(BaseModel):
    emailOrUsername: str
    password: str

class GoogleAuthModel(BaseModel):
    token: str


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def create_access_token(user_id: int, email: str):
    expire_time = datetime.now(timezone.utc) + timedelta(days=3)
    user_info = {"sub": str(user_id), "email": email, "exp": expire_time}
    return jwt.encode(user_info, JWT_SECRET_KEY, algorithm=ALGORITHM)

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/google")
async def google_authenticate(payload: GoogleAuthModel, session: Session = Depends(get_session)):
    user_info = verify_google_token(payload.token)
    
    if not user_info:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or expired Google token"
        )
    user = get_or_create_google_user(session, user_info)

    access_token = create_access_token(user.id, user.email)

    return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_pic": user.profile_pic
            }
        }

def get_current_user(authorization: str = Header(None)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid auth scheme. Expected 'Bearer'"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'"
        )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
            
        user_id = int(user_id_str)
        
    except PyJWTError:
        raise credentials_exception

    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            raise credentials_exception
        
        return user

@router.get("/getuser")
def get_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/register")
async def register_user(payload: RegisterPayload, session: Session = Depends(get_session)):
    if payload.password != payload.confirmPassword:
        raise HTTPException(status_code=400, detail = "Password doesn't match")
    
    
    try:
        existing_user = session.exec( select(User).where(or_(User.email == payload.emailOrUsername, User.username == payload.emailOrUsername))).first()
        raise HTTPException(status_code=400, detail="Email or Username already taken.")
    except Exception as e:
        print("Error in finding the existing user by the use of session: ", e)


    new_user = User(
        email = payload.email,
        username = payload.emailOrUsername,
        hashed_password = get_password_hash(payload.password)
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    token = create_access_token(new_user.id, new_user.email)

    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {"id": new_user.id, "username": new_user.username}
    }

@router.post("/login")
async def login_user(payload: LoginPayload, session: Session = Depends(get_session)):
    user = session.exec( select(User).where(or_(User.email == payload.emailOrUsername, User.username == payload.emailOrUsername))).first() 

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token(user.id, user.email)
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {"id": user.id, "username": user.username}
    }

    