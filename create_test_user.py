from src.logging.execution_logger import ExecutionLogger
from src.auth.auth_utils import hash_password
from datetime import datetime, timezone
import os
import sys

# Ensure src is in python path
sys.path.append(os.getcwd())

def create_user(email, password, display_name="Girish"):
    logger = ExecutionLogger(db_path="logs/agent_execution.db")
    
    with logger._connect() as conn:
        cursor = conn.cursor()
        
        # Check if user already exists
        try:
            cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                print(f"User {email} already exists")
                # Update password
                password_hash = hash_password(password)
                cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (password_hash, email))
                conn.commit()
                print(f"Password updated for {email}")
                return
        except Exception as e:
            print(f"Error checking user: {e}")
            return
        
        now = datetime.now(timezone.utc).isoformat()
        password_hash = hash_password(password)
        
        cursor.execute(
            """
            INSERT INTO users (
                email, display_name, password_hash,
                created_at, last_seen_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email, display_name, password_hash, now, now, 1),
        )
        conn.commit()
        print(f"User {email} created successfully")

if __name__ == "__main__":
    create_user("girish@julleyonline.in", "Girish@123")
