#================================#
#        DATABASE ENGINE         #
#================================#

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import DATABASE_URL


if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Add it to your environment or .env file.")


# --------------------------------
# Engine configuration
# --------------------------------
# Engine = core connection handler between app and database
# pool_pre_ping checks if a connection is alive before using it
engine_kwargs = {"pool_pre_ping": True}


# --------------------------------
# SQLite special configuration
# --------------------------------
# SQLite has a limitation where connections are tied to a single thread.
# FastAPI uses multiple threads, so we disable this restriction.
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}


# --------------------------------
# Create database engine
# --------------------------------
# This is the main entry point for all DB connections.
engine = create_engine(DATABASE_URL, **engine_kwargs)


# --------------------------------
# Session factory
# --------------------------------
# Session = a single database transaction context
# sessionmaker creates new sessions for each request
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,        # prevents automatic DB flush before queries
    autocommit=False,       # forces explicit commit
    expire_on_commit=False  # keeps objects usable after commit
)


# --------------------------------
# ORM base class
# --------------------------------
# All SQLAlchemy models inherit from this Base class
# It registers models and enables table creation via metadata
Base = declarative_base()


# --------------------------------
# Dependency: database session
# --------------------------------
# This function is used by FastAPI endpoints via Depends(get_db)
# It ensures each request gets its own DB session
def get_db() -> Generator[Session, None, None]:
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Provide session to the request
        yield db
    finally:
        # Always close session after request completes
        # Prevents connection leaks
        db.close()