"""User CRUD endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import get_current_user, hash_password
from app.database import get_session
from app.models import User, UserCreate, UserRead, UserUpdate
from app.schemas import ListResponseEnvelope, PaginationMeta, ResponseEnvelope

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=ResponseEnvelope[UserRead], status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[User]:
    """Create a new user."""
    # Check if user with this email already exists
    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hash_password(user_data.password),
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return ResponseEnvelope(data=user)


@router.get("/", response_model=ListResponseEnvelope[UserRead])
def list_users(
    offset: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> ListResponseEnvelope[User]:
    """List all users with pagination."""
    # Get total count for pagination metadata
    total_count = len(session.exec(select(User)).all())
    users = session.exec(select(User).offset(offset).limit(limit)).all()

    return ListResponseEnvelope(
        data=list(users),
        meta=PaginationMeta(offset=offset, limit=limit, total=total_count),
    )


@router.get("/{user_id}", response_model=ResponseEnvelope[UserRead])
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[User]:
    """Get a specific user by ID."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return ResponseEnvelope(data=user)


@router.patch("/{user_id}", response_model=ResponseEnvelope[UserRead])
def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[User]:
    """Update a user's information."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update only provided fields
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    user.updated_at = datetime.now(UTC)
    session.add(user)
    session.commit()
    session.refresh(user)
    return ResponseEnvelope(data=user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> None:
    """Delete a user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    session.delete(user)
    session.commit()
