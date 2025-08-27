#!/usr/bin/env python3
"""
Database data viewer for development.
"""

import sqlite3
from database.base import SessionLocal
from database.models import User, APIKey, ChatSession, ChatMessage
from datetime import datetime

def view_with_sqlite():
    """View data using direct SQLite connection."""
    print("=== DATABASE DATA (SQLite Direct) ===\n")
    
    conn = sqlite3.connect('data/dev.db')
    cursor = conn.cursor()
    
    tables = ['users', 'api_keys', 'chat_sessions', 'chat_messages']
    
    for table_name in tables:
        print(f"=== {table_name.upper()} TABLE ===")
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Records: {count}")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"Columns: {', '.join(columns)}")
            print("Data:")
            for row in rows:
                # Format row data nicely
                formatted_row = []
                for i, value in enumerate(row):
                    if isinstance(value, str) and len(value) > 50:
                        formatted_row.append(f"{value[:47]}...")
                    else:
                        formatted_row.append(str(value))
                print(f"  {dict(zip(columns, formatted_row))}")
        print()
    
    conn.close()

def view_with_sqlalchemy():
    """View data using SQLAlchemy ORM."""
    print("=== DATABASE DATA (SQLAlchemy ORM) ===\n")
    
    db = SessionLocal()
    try:
        # Users
        users = db.query(User).all()
        print(f"=== USERS ({len(users)} records) ===")
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Username: {user.username}")
            print(f"Active: {user.is_active}")
            print(f"Admin: {user.is_admin}")
            print(f"Failed Attempts: {user.failed_login_attempts}")
            print(f"Created: {user.created_at}")
            print(f"Last Login: {user.last_login}")
            print(f"Locked: {user.is_locked}")
            print("-" * 40)
        
        # API Keys
        api_keys = db.query(APIKey).all()
        print(f"\n=== API KEYS ({len(api_keys)} records) ===")
        for key in api_keys:
            print(f"ID: {key.id}")
            print(f"User ID: {key.user_id}")
            print(f"Provider: {key.provider}")
            print(f"Model: {key.model_name}")
            print(f"Active: {key.is_active}")
            print(f"Name: {key.name}")
            print(f"Usage Count: {key.usage_count}")
            print(f"Last Used: {key.last_used}")
            print(f"Created: {key.created_at}")
            print("-" * 40)
        
        # Chat Sessions
        sessions = db.query(ChatSession).all()
        print(f"\n=== CHAT SESSIONS ({len(sessions)} records) ===")
        for session in sessions:
            print(f"ID: {session.id}")
            print(f"Thread ID: {session.thread_id}")
            print(f"User ID: {session.user_id}")
            print(f"Provider: {session.provider}")
            print(f"Model: {session.model_name}")
            print(f"Title: {session.title}")
            print(f"Message Count: {session.message_count}")
            print(f"Total Tokens: {session.total_tokens}")
            print(f"Last Activity: {session.last_activity}")
            print(f"Active: {session.is_active}")
            print("-" * 40)
        
        # Chat Messages
        messages = db.query(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(10).all()
        print(f"\n=== RECENT CHAT MESSAGES ({len(messages)} of total) ===")
        for msg in messages:
            print(f"ID: {msg.id}")
            print(f"Session ID: {msg.session_id}")
            print(f"Role: {msg.role}")
            print(f"Content: {msg.content_preview}")
            print(f"Token Count: {msg.token_count}")
            print(f"Processing Time: {msg.processing_time_ms}ms")
            print(f"Error: {msg.is_error}")
            print(f"Created: {msg.created_at}")
            print("-" * 40)
    
    finally:
        db.close()

def view_specific_user(user_id=None, email=None):
    """View specific user and their related data."""
    db = SessionLocal()
    try:
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
        elif email:
            user = db.query(User).filter(User.email == email).first()
        else:
            user = db.query(User).first()  # Get first user
        
        if not user:
            print("No user found")
            return
        
        print(f"=== USER DETAILS ===")
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"Created: {user.created_at}")
        print(f"Is Active: {user.is_active}")
        print(f"Is Admin: {user.is_admin}")
        
        # User's API Keys
        print(f"\n=== USER'S API KEYS ({len(user.api_keys)}) ===")
        for key in user.api_keys:
            print(f"  {key.provider}/{key.model_name} - Used {key.usage_count} times")
        
        # User's Chat Sessions
        print(f"\n=== USER'S CHAT SESSIONS ({len(user.chat_sessions)}) ===")
        for session in user.chat_sessions:
            msg_count = len(session.messages)
            print(f"  {session.thread_id}: {session.provider}/{session.model_name} - {msg_count} messages")
    
    finally:
        db.close()

if __name__ == "__main__":
    try:
        view_with_sqlite()
        print("\n" + "="*60 + "\n")
        view_with_sqlalchemy()
        print("\n" + "="*60 + "\n")
        view_specific_user()
    except Exception as e:
        print(f"Error viewing data: {e}")
        import traceback
        traceback.print_exc()