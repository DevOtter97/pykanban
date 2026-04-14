"""Auth endpoints: user registration, login, and current-user lookup."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from auth import hash_password, verify_password, create_access_token, get_current_user
from models.user import UserCreate, UserOut
from models.auth import Token
from repositories.protocols import UserRepository
from repositories.sqlalchemy import get_user_repo

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Register a new user. Returns 400 if email or username is already taken."""
    if user_repo.get_by_email(user_data.email):
        logger.warning("registration_failed", reason="email_taken", email=user_data.email)
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_repo.get_by_username(user_data.username):
        logger.warning("registration_failed", reason="username_taken", username=user_data.username)
        raise HTTPException(status_code=400, detail="Username already taken")

    user = user_repo.create(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
    )
    logger.info("user_registered", user_id=user.id, username=user.username)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Authenticate with username/password and return a Bearer token."""
    hashed = user_repo.get_password_hash(form_data.username)
    if not hashed or not verify_password(form_data.password, hashed):
        logger.warning("login_failed", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": form_data.username})
    logger.info("user_logged_in", username=form_data.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def get_me(current_user: Annotated[UserOut, Depends(get_current_user)]):
    """Return the profile of the currently authenticated user."""
    return current_user
