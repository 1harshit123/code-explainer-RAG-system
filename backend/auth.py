import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from pwdlib import PasswordHash
from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, select, or_

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID")

from model import User 
from database import engine 

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()

class RegisterPayload(BaseModel):
    username: str
    email: str
    password: str
    confirmPassword: str

class LoginPayload(BaseModel):
    emailOrUsername: str
    password: str

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

def search_user_in_database(
        username: str,
        email: str,
        session: Session = Depends(get_session)
):
    existing_user = session.exec( select(User).where(or_(User.email == email, User.username == username))).first()

    return existing_user

def adding_new_user(new_user, session: Session = Depends(get_session)):
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return


@router.post("/register")
async def register_user(payload: RegisterPayload):
    if payload.password != payload.confirmPassword:
        return HTTPException(status_code=400, detail = "Password doesn't match")
    
    
    try:
        existing_user = search_user_in_database(payload.emailOrUsername, payload.email)
    except Exception as e:
        print("Error in finding the existing user by the use of session: ", e)

    

    if existing_user:
        raise HTTPException(status_code=400, detail="Email or Username already taken.")
    
    new_user = User(
        email = payload.email,
        username = payload.emailOrUsername,
        hashed_password = get_password_hash(payload.password)
    )

    adding_new_user(new_user)
    
    token = create_access_token(new_user.id, new_user.email)

    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {"id": new_user.id, "username": new_user.username}
    }

@router.post("/login")
async def login_user(payload: LoginPayload):
    user = search_user_in_database(payload.emailOrUsername, payload.email)

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token(user.id, user.email)
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {"id": user.id, "username": user.username}
    }

    