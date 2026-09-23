"""
ORM models for SQLModel database.
"""

import uuid
from datetime import UTC, datetime

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


def utc_now() -> datetime:
    """Return the current UTC time with timezone information."""
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    username: str = Field(unique=True, index=True, nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    # Relationships
    images: list["Image"] = Relationship(back_populates="user")
    predictions: list["Prediction"] = Relationship(back_populates="user")


class Image(SQLModel, table=True):
    __tablename__: str = "images"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", nullable=True)
    object_key: str = Field(nullable=False)
    original_filename: str | None = Field(default=None, nullable=True)
    content_type: str | None = Field(default=None, nullable=True)
    size_bytes: int | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    # Relationships
    user: User | None = Relationship(back_populates="images")
    predictions: list["Prediction"] = Relationship(back_populates="image")


class Prediction(SQLModel, table=True):
    __tablename__: str = "predictions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    image_id: uuid.UUID = Field(foreign_key="images.id", nullable=False)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", nullable=True)
    predicted_label: str = Field(nullable=False, index=True)
    confidence: float = Field(nullable=False)

    # Store JSON data in DB
    top_k: list[dict] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    recommendation: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))

    model_version: str | None = Field(default=None, nullable=True)
    latency_ms: float | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)

    # Relationships
    image: Image = Relationship(back_populates="predictions")
    user: User | None = Relationship(back_populates="predictions")
