from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from api.auth import decode_token, get_user_from_token, has_permission


security = HTTPBearer()


async def verify_token(token: str) -> dict:
    """Verify a JWT token and return user info"""
    try:
        user = await get_user_from_token(token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials =
        Depends(security),
):

    try:
        payload = decode_token(credentials.credentials)
        return {
            "username": payload["sub"],
            "role": payload["role"],
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def require_roles(*allowed_roles):
    """Dependency that checks for allowed roles"""
    def dependency(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return dependency


def require_permission(permission: str):
    """Dependency that checks for a specific permission"""
    def dependency(user=Depends(get_current_user)):
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires {permission}"
            )
        return user
    return dependency
