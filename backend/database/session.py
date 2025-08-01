"""
Database session management and dependency injection.
"""

import logging
from sqlalchemy.orm import Session
from fastapi import Depends
from .base import SessionLocal, engine, Base

logger = logging.getLogger(__name__)


def get_db() -> Session:
    """
    FastAPI dependency for database session.
    Ensures proper session lifecycle management.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    Should be called during application startup.
    """
    try:
        # Use checkfirst=True to avoid errors for existing tables/indexes
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        # If it's just an index that already exists, log but don't fail
        if "already exists" in str(e):
            logger.info("Database tables already exist - continuing")
        else:
            logger.error(f"Failed to create database tables: {e}")
            raise


def drop_tables():
    """
    Drop all database tables.
    Use with caution - for testing/development only.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise