"""JWT authentication utilities: password hashing, token creation, and user resolution."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt

from models.auth import TokenData
from models.user import UserOut
from repositories.sqlalchemy import get_user_repo, SqlUserRepository

logger = structlog.get_logger()

# In production, load this from environment variables
SECRET_KEY = "change-me-in-production-use-a-long-random-string"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plain-text password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against its bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict) -> str:
    """Create a signed JWT with an expiration claim."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: SqlUserRepository = Depends(get_user_repo),
) -> UserOut:
    """Decode the Bearer token and return the authenticated user, or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("auth_failed", reason="missing_sub_claim")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        logger.warning("auth_failed", reason="invalid_jwt")
        raise credentials_exception

    user = user_repo.get_by_username(token_data.username)
    if user is None:
        logger.warning("auth_failed", reason="user_not_found", username=token_data.username)
        raise credentials_exception
    return user
