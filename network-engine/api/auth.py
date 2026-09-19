import os
import jwt
import secrets
from typing import Optional

from datetime import datetime, timedelta, timezone
from database.connection import get_connection
from config import auth_config


JWT_SECRET = auth_config.jwt_secret
JWT_ALGORITHM = auth_config.jwt_algorithm
TOKEN_EXPIRE_MINUTES = auth_config.token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = auth_config.refresh_token_expire_days

# Role definitions
ROLES = {
    "ADMIN": "ADMIN",
    "OPERATOR": "OPERATOR", 
    "VIEWER": "VIEWER",
}

# Permissions matrix - what each role can do
PERMISSIONS = {
    "ADMIN": ["*"],  # All permissions
    "OPERATOR": [
        "monitor",
        "device:read",
        "device:write",  # limited
        "control:limits:read",
        "control:limits:write",
        "control:quotas:read", 
        "control:quotas:write",
        "control:rules:read",
        "control:rules:write",
        "control:firewall:read",
        "control:firewall:write",
        "settings:read",
        "settings:write",  # limited
        "reports:read",
        "system_operations",
    ],
    "VIEWER": [
        "monitor",
        "device:read",
        "control:limits:read",
        "control:quotas:read",
        "control:rules:read", 
        "control:firewall:read",
        "settings:read",
        "reports:read",
    ],
}

# Admin actions that require audit logging
AUDIT_ACTIONS = {
    "DELETE", "BLOCK", "UNBLOCK", "FIREWALL", "BACKUP", "RESTORE", 
    "SETTINGS", "USER_MANAGEMENT", "SYSTEM_OPERATIONS", "LIMITS", "QUOTAS"
}


def get_user_from_db(username: str) -> Optional[dict]:
    """Get user from database"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username, password_hash, role, is_active 
                FROM users WHERE username = %s
            """, (username,))
            row = cursor.fetchone()
            if row:
                return {
                    "username": row[0],
                    "password_hash": row[1],
                    "role": row[2],
                    "is_active": row[3]
                }
        return None
    finally:
        from database.connection import return_connection
        return_connection(connection)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user credentials"""
    user = get_user_from_db(username)
    
    if not user or not user["is_active"]:
        return None
    
    # Use bcrypt for password verification
    import bcrypt
    if not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        return None
    
    return {
        "username": user["username"],
        "role": user["role"],
    }


def create_access_token(username: str, role: str) -> str:
    """Create a JWT access token"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(username: str, role: str) -> str:
    """Create a JWT refresh token"""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    key = JWT_SECRET
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(token, str):
        token = token.encode('utf-8')
    return jwt.decode(token, key, algorithms=[JWT_ALGORITHM])


def get_user_from_token(token: str) -> dict:
    """Decode token and return user info"""
    payload = decode_token(token)
    return {
        "username": payload["sub"],
        "role": payload["role"],
    }


def has_permission(user: dict, permission: str) -> bool:
    """Check if user has a specific permission"""
    role = user.get("role", "VIEWER")
    role_perms = PERMISSIONS.get(role, [])
    return "*" in role_perms or permission in role_perms


def require_permission(permission: str):
    """Dependency that checks for a specific permission"""
    from fastapi import Depends, HTTPException, status
    from api.security import get_current_user
    
    def dependency(user=Depends(get_current_user)):
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires {permission}"
            )
        return user
    return dependency


def require_roles(*allowed_roles):
    """Dependency that checks for allowed roles"""
    from fastapi import Depends, HTTPException, status
    from api.security import get_current_user
    
    def dependency(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return dependency


def init_default_users():
    """Initialize default users in database"""
    import bcrypt
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Create users table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Default users from environment
            default_users = [
                ("admin", os.getenv("ADMIN_PASSWORD", "admin_change_me"), "ADMIN"),
                ("operator", os.getenv("OPERATOR_PASSWORD", "operator_change_me"), "OPERATOR"),
                ("viewer", os.getenv("VIEWER_PASSWORD", "viewer_change_me"), "VIEWER"),
            ]
            
            for username, password, role in default_users:
                # Check if user exists
                cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if not cursor.fetchone():
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, role)
                        VALUES (%s, %s, %s)
                    """, (username, password_hash, role))
            
            connection.commit()
    except Exception as e:
        connection.rollback()
        raise
    finally:
        return_connection(connection)
