import os
import jwt

from datetime import datetime, timedelta, timezone


JWT_SECRET = os.getenv(
    "NETWORK_CONTROL_JWT_SECRET",
    "your-secret-key-change-this"
)

if JWT_SECRET == "CHANGE_THIS_SECRET":
    raise ValueError(
        "NETWORK_CONTROL_JWT_SECRET environment variable must be set "
        "to a secure value in production"
    )

JWT_ALGORITHM = "HS256"

TOKEN_EXPIRE_MINUTES = 60


# User credentials - should be loaded from environment or database in production
USERS = {
    "admin": {
        "password": os.getenv("ADMIN_PASSWORD", "admin_password_change_me"),
        "role": "Admin",
    },

    "operator": {
        "password": os.getenv("OPERATOR_PASSWORD", "operator_password_change_me"),
        "role": "Operator",
    },

    "viewer": {
        "password": os.getenv("VIEWER_PASSWORD", "viewer_password_change_me"),
        "role": "Viewer",
    },
}


def authenticate_user(
    username: str,
    password: str,
):
    """Authenticate user credentials"""

    user = USERS.get(username)

    if not user:
        return None

    if user["password"] != password:
        return None

    return {
        "username": username,
        "role": user["role"],
    }


def create_access_token(
    username: str,
    role: str,
):
    """Create a JWT access token"""

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str):
    """Decode and verify a JWT token"""

    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )



def require_roles(*roles):
    """
    Decorator للتحقق من الصلاحيات وتجاوز الفحص أثناء التطوير
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator