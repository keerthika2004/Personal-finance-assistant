import base64
import hashlib
import json
import time
from fastapi import APIRouter, HTTPException, Header, Request, Depends, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.db.database import get_db
from backend.app.db.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = "User"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_token(user_id: str, email: str, name: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "exp": int(time.time()) + (30 * 24 * 3600)  # 30 days
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"demo_jwt_{encoded}"


def decode_token(token: str) -> Optional[dict]:
    if not token or not token.startswith("demo_jwt_"):
        return None
    try:
        raw = token.replace("demo_jwt_", "")
        data = json.loads(base64.b64decode(raw.encode()).decode())
        return data
    except Exception:
        return None


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> str:
    """Dependency helper to extract user_id from Authorization header or custom header."""
    if x_user_id:
        return x_user_id

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        decoded = decode_token(token)
        if decoded and "user_id" in decoded:
            return decoded["user_id"]

    return "demo_user"


@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email_clean = request.email.strip().lower()
    
    if not email_clean or "@" not in email_clean:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(request.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters long.")

    # Check if user already exists
    query = await db.execute(select(User).where(User.email == email_clean))
    existing_user = query.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="This email is already registered. Please sign in.")

    # Create new user
    new_user = User(
        email=email_clean,
        password_hash=hash_password(request.password),
        name=request.name.strip() if request.name else email_clean.split("@")[0].capitalize()
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_token(new_user.id, new_user.email, new_user.name)

    return {
        "status": "success",
        "access_token": token,
        "user": {
            "user_id": new_user.id,
            "email": new_user.email,
            "name": new_user.name
        }
    }


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    email_clean = request.email.strip().lower()
    
    query = await db.execute(select(User).where(User.email == email_clean))
    user = query.scalar_one_or_none()

    if not user or user.password_hash != hash_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. Please check your credentials."
        )

    token = create_token(user.id, user.email, user.name)

    return {
        "status": "success",
        "access_token": token,
        "user": {
            "user_id": user.id,
            "email": user.email,
            "name": user.name
        }
    }


@router.post("/demo")
async def demo_login():
    """1-Click Instant Demo Login for portfolio evaluation."""
    user_id = "demo_user"
    name = "Demo Portfolio Evaluator"
    email = "demo@financial-assistant.ai"
    token = create_token(user_id, email, name)

    return {
        "status": "success",
        "access_token": token,
        "user": {
            "user_id": user_id,
            "email": email,
            "name": name
        }
    }
