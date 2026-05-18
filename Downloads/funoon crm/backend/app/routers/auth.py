from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from jose import jwt
from pydantic import BaseModel

from app.config import settings
from app.dependencies.auth import get_current_user

router = APIRouter()

ALGORITHM = "HS256"


class LoginRequest(BaseModel):
    username: str
    password: str


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    if body.username != settings.admin_username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not bcrypt.checkpw(body.password.encode(), settings.admin_password_hash.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(body.username)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * settings.jwt_expire_days,
    )
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me")
async def me(username: str = Depends(get_current_user)):
    return {"username": username}
