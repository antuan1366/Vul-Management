from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import BOOTSTRAP_CREDENTIALS_FILENAME, require_admin
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth_security import hash_password


router = APIRouter(prefix="/api/users", tags=["User Administration"])


def _active_admin_count(db: Session) -> int:
    return int(
        db.query(func.count(User.id))
        .filter(User.role == "admin", User.is_active.is_(True))
        .scalar()
        or 0
    )


def _prevent_last_admin_lockout(db: Session, target: User, new_role, new_active) -> None:
    target_will_be_admin = new_role if new_role is not None else target.role
    target_will_be_active = new_active if new_active is not None else target.is_active
    if target.role == "admin" and target.is_active and (
        target_will_be_admin != "admin" or not target_will_be_active
    ):
        if _active_admin_count(db) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The last active administrator cannot be disabled, deleted, or demoted.",
            )


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return db.query(User).order_by(User.created_at.desc(), User.id.desc()).all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    user = User(
        username=data.username,
        display_name=data.display_name,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=data.is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That username already exists.",
        ) from error
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    changes = data.model_dump(exclude_unset=True)
    new_role = changes.get("role")
    new_active = changes.get("is_active")

    if user.id == admin.id and (new_role == "user" or new_active is False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot demote or disable your own account.",
        )

    _prevent_last_admin_lockout(db, user, new_role, new_active)

    password = changes.pop("password", None)
    if password:
        user.password_hash = hash_password(password)

    for field in ("display_name", "role", "is_active"):
        if field in changes and changes[field] is not None:
            setattr(user, field, changes[field])

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user could not be updated.",
        ) from error
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete the account you are currently using.",
        )

    _prevent_last_admin_lockout(db, user, new_role="user", new_active=False)
    username = user.username
    db.delete(user)
    db.commit()
    if username == settings.bootstrap_admin_username.strip().lower():
        try:
            (settings.data_dir / BOOTSTRAP_CREDENTIALS_FILENAME).unlink(missing_ok=True)
        except OSError:
            pass
