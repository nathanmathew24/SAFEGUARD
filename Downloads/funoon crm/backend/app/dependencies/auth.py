from fastapi import Cookie, HTTPException, status
from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


def get_current_user(access_token: str | None = Cookie(default=None)) -> str:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(access_token, settings.jwt_secret, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
