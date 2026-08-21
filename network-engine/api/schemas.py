from pydantic import BaseModel, Field
from typing import Optional


class DeviceLimitRequest(BaseModel):
    download_limit: Optional[int] = Field(
        default=None,
        ge=0,
    )

    upload_limit: Optional[int] = Field(
        default=None,
        ge=0,
    )


class DeviceQuotaRequest(BaseModel):
    quota_bytes: int = Field(
        gt=0,
    )


class DeviceNameRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )


class BlockRequest(BaseModel):
    reason: Optional[str] = Field(
        default=None,
        max_length=255,
    )


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"