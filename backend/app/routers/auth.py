"""
Authentication routes for user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from backend.app.config import settings
from backend.app.db import crud, get_session
from backend.app.models.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from backend.app.security import (
    bearer_scheme,
    blacklist_token,
    create_access_token,
    get_current_user,
)
from backend.app.services.limiter import RateLimiter

router = APIRouter(prefix="/auth", tags=["auth"])
login_rate_limiter = RateLimiter(
    times=settings.RATE_LIMIT_LOGIN_PER_MINUTE,
    seconds=60,
    key_prefix="login",
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    if crud.get_user_by_username(session, payload.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    try:
        return crud.create_user(session, payload.username, payload.email, payload.password)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists") from exc


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    session: Session = Depends(get_session),
    _rate_limit: None = Depends(login_rate_limiter),
):
    user = crud.get_user_by_username(session, payload.username)
    if user is None or not crud.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserResponse)
def read_me(current_user=Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(credentials=Depends(bearer_scheme)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    blacklist_token(credentials.credentials)
    return {"message": "Successfully logged out"}
