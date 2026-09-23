"""
CRUD (Create, Read, Update, Delete) operations using SQLModel.
"""

import uuid

import bcrypt
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from backend.app.db.orm_models import Image, Prediction, User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed representation."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


# --- User CRUD ---


def create_user(session: Session, username: str, email: str, password: str) -> User:
    """Create a new user with hashed password."""
    hashed_pwd = hash_password(password)
    db_user = User(username=username, email=email, hashed_password=hashed_pwd)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_username(session: Session, username: str) -> User | None:
    """Retrieve a user by their username."""
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()


def get_user_by_id(session: Session, user_id: uuid.UUID) -> User | None:
    """Retrieve a user by their ID."""
    return session.get(User, user_id)


# --- Image CRUD ---


def create_image_record(
    session: Session,
    object_key: str,
    user_id: uuid.UUID | None = None,
    original_filename: str | None = None,
    content_type: str | None = None,
    size_bytes: int | None = None,
    commit: bool = True,
) -> Image:
    """Save upload metadata for an image."""
    db_image = Image(
        user_id=user_id,
        object_key=object_key,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=size_bytes,
    )
    session.add(db_image)
    if commit:
        session.commit()
        session.refresh(db_image)
    else:
        session.flush()
    return db_image


def get_image_by_id(session: Session, image_id: uuid.UUID) -> Image | None:
    """Retrieve an image record by its ID."""
    return session.get(Image, image_id)


# --- Prediction CRUD ---


def create_prediction_record(
    session: Session,
    image_id: uuid.UUID,
    predicted_label: str,
    confidence: float,
    top_k: list[dict],
    user_id: uuid.UUID | None = None,
    recommendation: dict | None = None,
    model_version: str | None = None,
    latency_ms: float | None = None,
    commit: bool = True,
) -> Prediction:
    """Save prediction details."""
    db_prediction = Prediction(
        image_id=image_id,
        user_id=user_id,
        predicted_label=predicted_label,
        confidence=confidence,
        top_k=top_k,
        recommendation=recommendation,
        model_version=model_version,
        latency_ms=latency_ms,
    )
    session.add(db_prediction)
    if commit:
        session.commit()
        session.refresh(db_prediction)
    else:
        session.flush()
    return db_prediction


def get_predictions_by_user(
    session: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 10,
) -> list[Prediction]:
    """Retrieve history of predictions for a given user with pagination."""
    statement = (
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .options(joinedload(Prediction.image))
        .order_by(Prediction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_prediction_detail(session: Session, prediction_id: uuid.UUID) -> Prediction | None:
    """Retrieve detailed prediction log by ID."""
    return session.get(Prediction, prediction_id)
