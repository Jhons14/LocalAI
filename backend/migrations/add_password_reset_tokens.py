"""
Database migration script to add password_reset_tokens table.
This script adds the new table for handling forgotten password functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config.settings import get_settings
from database.base import Base
from database.models import User, PasswordResetToken

def run_migration():
    """Run the migration to add password_reset_tokens table."""
    settings = get_settings()
    
    print("🔄 Starting password reset tokens migration...")
    print(f"Database URL: {settings.database.url}")
    
    try:
        # Create engine
        engine = create_engine(settings.database.url, echo=settings.database.echo)
        
        # Create tables (this will only create missing tables)
        print("📋 Creating password_reset_tokens table...")
        Base.metadata.create_all(engine)
        
        # Verify the table was created (works for both PostgreSQL and SQLite)
        with engine.connect() as connection:
            # Use a query that works for both PostgreSQL and SQLite
            if "postgresql" in settings.database.url:
                # PostgreSQL query
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'password_reset_tokens'
                """))
            else:
                # SQLite query
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='password_reset_tokens'
                """))
            
            if result.fetchone():
                print("✅ password_reset_tokens table created successfully!")
            else:
                print("❌ Failed to create password_reset_tokens table")
                return False
        
        print("🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)