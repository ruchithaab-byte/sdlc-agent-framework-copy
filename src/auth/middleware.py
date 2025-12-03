"""
Authentication middleware for protecting API endpoints.
"""

from __future__ import annotations

from typing import Callable, Optional

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from src.auth.auth_utils import get_user_from_token
from src.logging.execution_logger import ExecutionLogger


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from request Authorization header.
    
    Args:
        request: aiohttp request object
        
    Returns:
        Token string or None
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def require_auth() -> Callable:
    """
    Decorator to require authentication for an endpoint.
    
    Usage:
        @require_auth()
        async def my_handler(request):
            user_email = request['user_email']
            ...
            
        Or for instance methods:
        @require_auth()
        async def my_handler(self, request):
            user_email = request['user_email']
            ...
    """
    def decorator(handler: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Response:
            # Determine if this is an instance method (first arg is self) or regular function
            # For aiohttp, the request is always the last positional arg
            request = None
            if args:
                # Check if first arg is a Request object
                if isinstance(args[0], Request):
                    request = args[0]
                    handler_args = args
                else:
                    # Instance method - request is second arg
                    request = args[1] if len(args) > 1 else None
                    handler_args = args
            else:
                # Try to get from kwargs
                request = kwargs.get('request')
                handler_args = args
            
            if not request or not isinstance(request, Request):
                return web.json_response(
                    {"error": "Invalid request"}, status=400
                )
            
            token = get_token_from_request(request)
            if not token:
                return web.json_response(
                    {"error": "Authentication required"}, status=401
                )
            
            user_info = get_user_from_token(token)
            if not user_info:
                return web.json_response(
                    {"error": "Invalid or expired token"}, status=401
                )
            
            # Check token revocation status
            logger = ExecutionLogger()
            with logger._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT is_revoked FROM user_sessions
                    WHERE id = ? AND user_email = ?
                    """,
                    (user_info["jti"], user_info["email"]),
                )
                row = cursor.fetchone()
                if row and row[0]:
                    return web.json_response(
                        {"error": "Token has been revoked"}, status=401
                    )
            
            # Inject user info into request
            request["user_email"] = user_info["email"]
            request["is_admin"] = user_info["is_admin"]
            request["jti"] = user_info["jti"]
            
            return await handler(*handler_args, **kwargs)
        
        return wrapper
    return decorator


def require_admin() -> Callable:
    """
    Decorator to require admin privileges for an endpoint.
    Must be used after @require_auth()
    """
    def decorator(handler: Callable) -> Callable:
        async def wrapper(request: Request) -> Response:
            if not request.get("is_admin", False):
                return web.json_response(
                    {"error": "Admin privileges required"}, status=403
                )
            return await handler(request)
        
        return wrapper
    return decorator


__all__ = ["require_auth", "require_admin", "get_token_from_request"]

