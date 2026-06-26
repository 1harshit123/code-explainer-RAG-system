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

class RegisterPayload(BaseModel):
    emailOrUsername: str
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




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

@router.get("/getuser")
def getUser(authorization: str) -> User:
    return get_current_user(authorization=authorization)


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

    