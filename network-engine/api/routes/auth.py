from fastapi import APIRouter, HTTPException

from api.schemas import (
    LoginRequest,
    TokenResponse,
)

from api.auth import (
    authenticate_user,
    create_access_token,
)


router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(data: LoginRequest):

    user = authenticate_user(
        data.username,
        data.password,
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    token = create_access_token(
        user["username"],
        user["role"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }

