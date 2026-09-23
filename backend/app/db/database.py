"""
Database connection and session helper functions using SQLModel.
"""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from backend.app.config import settings

# In production we might want pool settings, but for dev and simplicity,
# create_engine using the database url is sufficient.
engine = create_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL query logging if debugging
)


def init_db() -> None:
    """
    Initializes database tables defined in orm_models.
    Typically used for local development. In production, Alembic migrations should be used.
    """
    # Import ORM models so they are registered with SQLModel.metadata
    from backend.app.db import orm_models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency generator yielding a database session.
    """
    with Session(engine) as session:
        yield session
