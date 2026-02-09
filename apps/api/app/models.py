"""Database models using SQLModel."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User model for demonstration purposes.

    This is a simple example model to demonstrate SQLModel usage
    and database operations in Step 3.
    """

    __tablename__ = "users"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=255)
    # Nullable for smooth migration; auth flows require this to be set.
    password_hash: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserCreate(SQLModel):
    """Schema for creating a new user."""

    email: str = Field(max_length=255)
    name: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=1024)


class UserUpdate(SQLModel):
    """Schema for updating an existing user."""

    email: str | None = Field(default=None, max_length=255)
    name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class UserRead(SQLModel):
    """Schema for reading user data (public response)."""

    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RefreshToken(SQLModel, table=True):
    """Refresh token allowlist to support rotation/revocation (refresh/logout)."""

    __tablename__ = "refresh_tokens"  # type: ignore[assignment]

    # JWT ID ("jti") is the primary key so we can revoke/lookup quickly.
    jti: str = Field(primary_key=True, max_length=64)
    user_id: int = Field(foreign_key="users.id", index=True)
    expires_at: datetime = Field(index=True)
    revoked_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
