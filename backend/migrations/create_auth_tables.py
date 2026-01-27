"""
Database migration script to create authentication tables.
This script creates all necessary tables for the authentication system.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings
from database.base import Base
from database.models import User, PasswordResetToken


def create_auth_tables():
    """Create all authentication-related tables"""
    settings = get_settings()
    
    if not settings.database.url:
        print("❌ No database URL configured. Skipping database table creation.")
        return False
    
    try:
        # Create engine
        engine = create_engine(settings.database.url)
        
        print(f"🔗 Connecting to database: {settings.database.url}")
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Create all tables
        print("📋 Creating authentication tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            # Check for main tables
            tables_to_check = ['users', 'password_reset_tokens']
            existing_tables = []
            
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    existing_tables.append(table)
                except SQLAlchemyError:
                    print(f"⚠️  Table '{table}' not found or not accessible")
            
            print(f"✅ Created/verified tables: {', '.join(existing_tables)}")
        
        print("🎉 Authentication database setup completed successfully!")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def create_indexes():
    """Create additional indexes for performance"""
    settings = get_settings()
    
    if not settings.database.url:
        return False
    
    try:
        engine = create_engine(settings.database.url)
        
        # Additional performance indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_users_login_attempts ON users(failed_login_attempts, locked_until);"
        ]
        
        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                    print(f"✅ Created index: {index_sql.split()[5]}")
                except SQLAlchemyError as e:
                    print(f"⚠️  Index creation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting authentication database migration...")
    
    # Create tables
    tables_created = create_auth_tables()
    
    if tables_created:
        # Create additional indexes
        print("\n📊 Creating performance indexes...")
        create_indexes()
        
        print("\n✅ Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Start the FastAPI server: python main.py")
        print("2. Register a new user: POST /auth/register")
        print("3. Login to get JWT tokens: POST /auth/login")
        print("4. Use authenticated endpoints with Authorization header")
    else:
        print("\n❌ Migration failed. Please check the database configuration.")
        sys.exit(1)