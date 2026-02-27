from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..security.passwords import hash_password, verify_password
from ..security.jwt import create_access_token
from ..security.rate_limit import ratelimit_or_429

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(409, "Email already registered")
    u = User(email=body.email, password_hash=hash_password(body.password), scopes="accounts:read transfers:write")
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "email": u.email}

@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    # basic brute-force protection by email
    if not ratelimit_or_429(f"login:{body.email.lower()}"):
        raise HTTPException(429, "Too many attempts")

    u = db.query(User).filter(User.email == body.email).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Invalid credentials")

    scopes = (u.scopes or "").split()
    token = create_access_token(sub=str(u.id), scopes=scopes)
    return {"access_token": token, "token_type": "bearer", "scopes": scopes}