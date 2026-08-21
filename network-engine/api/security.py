from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from api.auth import decode_token


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials =
        Depends(security),
):

    try:

        payload = decode_token(
            credentials.credentials
        )

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

    def dependency(
        user=Depends(get_current_user),
    ):

        if user["role"] not in allowed_roles:

            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )

        return user

    return dependency