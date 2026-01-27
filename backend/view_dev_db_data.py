#!/usr/bin/env python3
"""
Database data viewer for development.
"""

import sqlite3
from database.base import SessionLocal
from database.models import User, PasswordResetToken
from datetime import datetime

def view_with_sqlite():
    """View data using direct SQLite connection."""
    print("=== DATABASE DATA (SQLite Direct) ===\n")
    
    conn = sqlite3.connect('data/dev.db')
    cursor = conn.cursor()
    
    tables = ['users', 'password_reset_tokens']
    
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
        
        # Password Reset Tokens
        tokens = db.query(PasswordResetToken).all()
        print(f"\n=== PASSWORD RESET TOKENS ({len(tokens)} records) ===")
        for token in tokens:
            print(f"ID: {token.id}")
            print(f"User ID: {token.user_id}")
            print(f"Token: {token.token[:16]}...")
            print(f"Expires: {token.expires_at}")
            print(f"Is Used: {token.is_used}")
            print(f"Used At: {token.used_at}")
            print(f"Requested IP: {token.requested_ip}")
            print(f"Created: {token.created_at}")
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
        
        # User's Password Reset Tokens
        print(f"\n=== USER'S PASSWORD RESET TOKENS ({len(user.password_reset_tokens)}) ===")
        for token in user.password_reset_tokens:
            status = "Used" if token.is_used else "Expired" if token.is_expired else "Active"
            print(f"  {token.token[:16]}... - {status} - Created: {token.created_at}")
    
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