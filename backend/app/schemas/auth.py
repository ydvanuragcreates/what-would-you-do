import uuid
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    field_validator,
)

Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$"
    ),
]


class RegisterRequest(BaseModel):
    # Unknown fields are rejected instead of silently ignored.
    model_config = ConfigDict(extra="forbid")

    username: Username
    email: EmailStr
    # SecretStr: never printed by accident in logs or error messages.
    # No "must contain a symbol" rules; length matters far more than composition.
    # The upper limit stops someone submitting a 10 MB "password" to burn CPU on hashing.
    password: SecretStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def check_password_length(cls, value: SecretStr) -> SecretStr:
        # A hand-written check because pydantic's built-in message for SecretStr
        # length says "items", which is confusing for a player.
        if not 8 <= len(value.get_secret_value()) <= 128:
            raise ValueError("Password must be between 8 and 128 characters.")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Plain str (not EmailStr) so any bad login is a uniform 401, never a format error.
    email: str = Field(max_length=255)
    password: SecretStr = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserPublic(BaseModel):
    """What the API is allowed to say about a user. password_hash cannot leak because it
    is not a field here."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    created_at: datetime
