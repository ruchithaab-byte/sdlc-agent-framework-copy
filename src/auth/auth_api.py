"""
Authentication API endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from src.auth.auth_utils import (
    generate_jwt_token,
    hash_password,
    verify_password,
)
from src.auth.middleware import require_auth
from src.logging.execution_logger import ExecutionLogger
from src.utils.user_utils import validate_email, validate_password_strength


class AuthAPI:
    """Authentication API endpoints."""
    
    def __init__(self, db_path: str = "logs/agent_execution.db"):
        self.db_path = db_path
    
    async def register(self, request: Request) -> Response:
        """POST /api/auth/register - Register a new user."""
        try:
            data = await request.json()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            display_name = data.get("display_name", "").strip()
            
            if not email:
                return web.json_response(
                    {"error": "Email is required"}, status=400
                )
            
            if not password:
                return web.json_response(
                    {"error": "Password is required"}, status=400
                )
            
            # Validate email format
            if not validate_email(email):
                return web.json_response(
                    {"error": "Invalid email format"}, status=400
                )
            
            # Validate password strength
            is_valid, error_msg = validate_password_strength(password)
            if not is_valid:
                return web.json_response(
                    {"error": error_msg}, status=400
                )
            
            logger = ExecutionLogger(db_path=self.db_path)
            with logger._connect() as conn:
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute(
                    "SELECT email FROM users WHERE email = ?", (email,)
                )
                if cursor.fetchone():
                    return web.json_response(
                        {"error": "User already exists"}, status=409
                    )
                
                # Create user
                now = datetime.now(timezone.utc).isoformat()
                password_hash = hash_password(password)
                
                cursor.execute(
                    """
                    INSERT INTO users (
                        email, display_name, password_hash,
                        created_at, last_seen_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (email, display_name or email, password_hash, now, now, 1),
                )
                conn.commit()
            
            return web.json_response(
                {
                    "message": "User created successfully",
                    "user": {"email": email, "display_name": display_name or email},
                },
                status=201,
            )
        
        except Exception as e:
            return web.json_response(
                {"error": f"Registration failed: {str(e)}"}, status=500
            )
    
    async def login(self, request: Request) -> Response:
        """POST /api/auth/login - Authenticate user and get JWT token."""
        try:
            # Check JWT_SECRET is set
            from src.auth.auth_utils import get_jwt_secret
            try:
                get_jwt_secret()
            except RuntimeError as e:
                return web.json_response(
                    {"error": "Server configuration error: JWT_SECRET not set"}, status=500
                )
            
            data = await request.json()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            
            if not email or not password:
                return web.json_response(
                    {"error": "Email and password are required"}, status=400
                )
            
            logger = ExecutionLogger(db_path=self.db_path)
            with logger._connect() as conn:
                cursor = conn.cursor()
                
                # Get user
                cursor.execute(
                    """
                    SELECT email, password_hash, display_name, is_admin, is_active
                    FROM users WHERE email = ?
                    """,
                    (email,),
                )
                row = cursor.fetchone()
                
                if not row:
                    return web.json_response(
                        {"error": "Invalid email or password"}, status=401
                    )
                
                user_email, password_hash, display_name, is_admin, is_active = row
                
                if not is_active:
                    return web.json_response(
                        {"error": "Account is disabled"}, status=403
                    )
                
                # Verify password
                if not verify_password(password, password_hash):
                    return web.json_response(
                        {"error": "Invalid email or password"}, status=401
                    )
                
                # Generate JWT token
                token, jti = generate_jwt_token(user_email, bool(is_admin))
                
                # Store session
                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(hours=24)
                
                cursor.execute(
                    """
                    INSERT INTO user_sessions (
                        id, user_email, token_hash, created_at, expires_at, last_used_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        jti,
                        user_email,
                        jti,  # Using jti as token_hash for simplicity
                        now.isoformat(),
                        expires_at.isoformat(),
                        now.isoformat(),
                    ),
                )
                
                # Update user last_login_at
                cursor.execute(
                    "UPDATE users SET last_login_at = ?, last_seen_at = ? WHERE email = ?",
                    (now.isoformat(), now.isoformat(), user_email),
                )
                
                conn.commit()
            
            return web.json_response(
                {
                    "token": token,
                    "user_email": user_email,
                    "display_name": display_name or user_email,
                    "is_admin": bool(is_admin),
                    "expires_at": expires_at.isoformat(),
                },
                status=200,
            )
        
        except Exception as e:
            return web.json_response(
                {"error": f"Login failed: {str(e)}"}, status=500
            )
    
    @require_auth()
    async def logout(self, request: Request) -> Response:
        """POST /api/auth/logout - Revoke current token."""
        try:
            jti = request.get("jti")
            if not jti:
                return web.json_response(
                    {"error": "Token not found"}, status=400
                )
            
            logger = ExecutionLogger(db_path=self.db_path)
            with logger._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE user_sessions SET is_revoked = 1 WHERE id = ?",
                    (jti,),
                )
                conn.commit()
            
            return web.json_response({"message": "Logged out successfully"}, status=200)
        
        except Exception as e:
            return web.json_response(
                {"error": f"Logout failed: {str(e)}"}, status=500
            )
    
    @require_auth()
    async def me(self, request: Request) -> Response:
        """GET /api/auth/me - Get current user info."""
        try:
            user_email = request.get("user_email")
            
            logger = ExecutionLogger(db_path=self.db_path)
            with logger._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT email, display_name, is_admin, created_at, last_login_at
                    FROM users WHERE email = ?
                    """,
                    (user_email,),
                )
                row = cursor.fetchone()
                
                if not row:
                    return web.json_response(
                        {"error": "User not found"}, status=404
                    )
                
                return web.json_response(
                    {
                        "email": row[0],
                        "display_name": row[1],
                        "is_admin": bool(row[2]),
                        "created_at": row[3],
                        "last_login_at": row[4],
                    },
                    status=200,
                )
        
        except Exception as e:
            return web.json_response(
                {"error": f"Failed to get user info: {str(e)}"}, status=500
            )
    
    def setup_routes(self, app: web.Application) -> None:
        """Register authentication routes."""
        app.router.add_post("/api/auth/register", self.register)
        app.router.add_post("/api/auth/login", self.login)
        app.router.add_post("/api/auth/logout", self.logout)
        app.router.add_get("/api/auth/me", self.me)


__all__ = ["AuthAPI"]

