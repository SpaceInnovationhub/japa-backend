#!/usr/bin/env python3
"""
Password Hash Corruption Fixer
Run this script to identify and optionally fix corrupted password hashes in your database.
"""

import os
import sys
import logging
from typing import List, Dict
from sqlalchemy import text

# Add the current directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import User
from app.auth import hash_password, verify_password

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('password_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_corrupted_hashes() -> List[Dict]:
    """Identify all users with corrupted password hashes"""
    db = SessionLocal()
    corrupted_users = []
    
    try:
        # Get total user count
        total_users = db.query(User).count()
        logger.info(f"🔍 Checking {total_users} users for corrupted password hashes...")
        
        users = db.query(User).all()
        
        for user in users:
            issues = []
            
            if not user.password:
                issues.append("No password hash")
            else:
                # Check hash length (bcrypt should be 60 characters)
                if len(user.password) != 60:
                    issues.append(f"Invalid length: {len(user.password)} (expected 60)")
                
                # Check bcrypt format (should start with $2a$, $2b$, or $2y$)
                if not user.password.startswith(('$2a$', '$2b$', '$2y$')):
                    issues.append(f"Invalid format: starts with '{user.password[:4]}' (expected $2a$, $2b$, or $2y$)")
                
                # Check for valid characters (bcrypt uses base64)
                import re
                if not re.match(r'^\$2[aby]\$\d+\$[./A-Za-z0-9]{53}$', user.password):
                    issues.append("Invalid bcrypt format pattern")
            
            if issues:
                corrupted_users.append({
                    "id": user.id,
                    "email": user.email,
                    "fullname": user.fullname,
                    "hash_preview": user.password[:20] if user.password else "None",
                    "hash_length": len(user.password) if user.password else 0,
                    "issues": issues
                })
                logger.warning(f"⚠️  User {user.email} (ID: {user.id}) has corrupted hash: {', '.join(issues)}")
        
        logger.info(f"✅ Scan complete. Found {len(corrupted_users)} corrupted hashes out of {total_users} users.")
        
    except Exception as e:
        logger.error(f"❌ Error checking hashes: {str(e)}")
    finally:
        db.close()
    
    return corrupted_users

def print_corrupted_users_report(corrupted_users: List[Dict]):
    """Print a formatted report of corrupted users"""
    if not corrupted_users:
        print("\n" + "="*60)
        print("✅ NO CORRUPTED PASSWORD HASHES FOUND!")
        print("="*60)
        return
    
    print("\n" + "="*60)
    print(f"📋 CORRUPTED PASSWORD HASHES REPORT ({len(corrupted_users)} users)")
    print("="*60)
    
    for idx, user in enumerate(corrupted_users, 1):
        print(f"\n{idx}. User ID: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Name: {user['fullname']}")
        print(f"   Hash Length: {user['hash_length']}")
        print(f"   Hash Preview: {user['hash_preview']}...")
        print(f"   Issues: {', '.join(user['issues'])}")
    
    print("\n" + "="*60)

def fix_single_user(user_id: int, new_password: str = None):
    """Fix a single user's password hash"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return False
        
        # Generate new password
        if not new_password:
            import secrets
            import string
            # Generate a random temporary password
            alphabet = string.ascii_letters + string.digits
            new_password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Hash the new password
        hashed = hash_password(new_password)
        
        # Validate the new hash
        if len(hashed) != 60 or not hashed.startswith('$2'):
            logger.error(f"Generated hash is invalid for user {user.email}")
            return False
        
        # Update the user
        old_hash = user.password
        user.password = hashed
        db.commit()
        
        logger.info(f"✅ Fixed password for {user.email}")
        logger.info(f"   Temporary password: {new_password}")
        logger.info(f"   Please have the user change this immediately!")
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error fixing user {user_id}: {str(e)}")
        return False
    finally:
        db.close()

def fix_all_corrupted_users(interactive: bool = True):
    """Fix all corrupted users interactively or automatically"""
    corrupted_users = check_corrupted_hashes()
    
    if not corrupted_users:
        print("\n✅ No corrupted users to fix!")
        return
    
    print_corrupted_users_report(corrupted_users)
    
    if not interactive:
        # Auto-fix all users with temporary passwords
        print("\n🔧 Auto-fixing all corrupted users...")
        fixed = 0
        for user in corrupted_users:
            if fix_single_user(user['id']):
                fixed += 1
        print(f"\n✅ Fixed {fixed}/{len(corrupted_users)} users")
        return
    
    # Interactive mode
    print("\n🔧 What would you like to do?")
    print("1. Fix a specific user")
    print("2. Fix all users (generates temporary passwords)")
    print("3. Export list to CSV (for support team)")
    print("4. Exit without fixing")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        user_id = input("Enter user ID to fix: ").strip()
        if user_id.isdigit():
            custom_pass = input("Enter custom password (or press Enter for auto-generated): ").strip()
            fix_single_user(int(user_id), custom_pass if custom_pass else None)
        else:
            print("❌ Invalid user ID")
    
    elif choice == '2':
        confirm = input("⚠️  This will reset passwords for ALL corrupted users. Continue? (yes/no): ").strip().lower()
        if confirm == 'yes':
            for user in corrupted_users:
                fix_single_user(user['id'])
        else:
            print("Operation cancelled")
    
    elif choice == '3':
        import csv
        with open('corrupted_users.csv', 'w', newline='') as csvfile:
            fieldnames = ['id', 'email', 'fullname', 'hash_length', 'issues']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user in corrupted_users:
                writer.writerow({
                    'id': user['id'],
                    'email': user['email'],
                    'fullname': user['fullname'],
                    'hash_length': user['hash_length'],
                    'issues': ', '.join(user['issues'])
                })
        print("✅ Exported corrupted users to 'corrupted_users.csv'")
    
    else:
        print("Exiting without making changes")

def create_password_reset_endpoint():
    """Print SQL to create a password reset tracking table (optional)"""
    sql = """
    -- Create a password reset tokens table for better security
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        token VARCHAR(255) UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create index for faster lookups
    CREATE INDEX IF NOT EXISTS idx_reset_token ON password_reset_tokens(token);
    CREATE INDEX IF NOT EXISTS idx_reset_expires ON password_reset_tokens(expires_at);
    """
    print("\n📝 Optional: Run this SQL to create a password reset tokens table:")
    print(sql)

if __name__ == "__main__":
    print("="*60)
    print("🔐 PASSWORD HASH CORRUPTION FIXER")
    print("="*60)
    print("\nThis script will help you:")
    print("- Identify users with corrupted password hashes")
    print("- Fix individual or all corrupted passwords")
    print("- Generate temporary passwords for affected users")
    print("\n⚠️  Make sure you have a database backup before running!")
    print("="*60)
    
    confirm = input("\nDo you want to continue? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Exiting...")
        sys.exit(0)
    
    # Check if running in auto mode
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        fix_all_corrupted_users(interactive=False)
    else:
        fix_all_corrupted_users(interactive=True)
    
    # Optional: Show SQL for reset tokens table
    show_sql = input("\nWould you like to see the SQL for creating a password reset tokens table? (yes/no): ").strip().lower()
    if show_sql == 'yes':
        create_password_reset_endpoint()