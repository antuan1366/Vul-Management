import threading
import time
from datetime import datetime
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import SessionLocal, engine, get_db
from app.models.user import User
from app.schemas.auth import InitialAdminSetup, LoginRequest
from app.schemas.user import UserResponse
from app.services.auth_security import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    create_session_token,
    get_session_user_id,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["Authentication"])
_failed_login_attempts: dict[str, list[float]] = {}
_attempts_lock = threading.Lock()
_MAX_FAILED_ATTEMPTS = 10
_ATTEMPT_WINDOW_SECONDS = 300


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = get_session_user_id(request.cookies.get(SESSION_COOKIE_NAME))
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is no longer valid. Please sign in again.",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission is required.",
        )
    return user


def active_session_user_id(request: Request) -> int | None:
    user_id = get_session_user_id(request.cookies.get(SESSION_COOKIE_NAME))
    if user_id is None:
        return None

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user is None or not user.is_active:
            return None
        return user.id
    finally:
        db.close()


def users_exist() -> bool:
    db = SessionLocal()
    try:
        return db.query(User.id).first() is not None
    finally:
        db.close()


def set_session_cookie(response: Response, request: Request, user_id: int) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(user_id),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown-client"


def _is_rate_limited(client_key: str) -> bool:
    now = time.monotonic()
    with _attempts_lock:
        recent = [
            attempt
            for attempt in _failed_login_attempts.get(client_key, [])
            if now - attempt < _ATTEMPT_WINDOW_SECONDS
        ]
        _failed_login_attempts[client_key] = recent
        return len(recent) >= _MAX_FAILED_ATTEMPTS


def _record_failed_login(client_key: str) -> None:
    now = time.monotonic()
    with _attempts_lock:
        recent = [
            attempt
            for attempt in _failed_login_attempts.get(client_key, [])
            if now - attempt < _ATTEMPT_WINDOW_SECONDS
        ]
        recent.append(now)
        _failed_login_attempts[client_key] = recent


def _clear_failed_logins(client_key: str) -> None:
    with _attempts_lock:
        _failed_login_attempts.pop(client_key, None)


def _safe_redirect_target(target: str | None) -> str:
    if not target or not target.startswith("/src/pages/"):
        return "/src/pages/dashboard.html"
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.path.startswith("//") or ".." in parsed.path:
        return "/src/pages/dashboard.html"
    if not parsed.path.endswith(".html"):
        return "/src/pages/dashboard.html"
    return target


def _create_first_admin(data: InitialAdminSetup) -> int:
    now = datetime.utcnow()
    password_hash = hash_password(data.password)
    connection = engine.connect()

    try:
        if settings.database_url and settings.database_url.startswith("sqlite"):
            # Serialize first-run setup so only one concurrent request can claim it.
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            connection.begin()

        user_count = connection.execute(
            select(func.count()).select_from(User.__table__)
        ).scalar_one()
        if user_count:
            connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Initial setup has already been completed. Please sign in.",
            )

        result = connection.execute(
            insert(User.__table__).values(
                username=data.username,
                display_name=data.display_name,
                password_hash=password_hash,
                role="admin",
                is_active=True,
                created_at=now,
                updated_at=now,
                last_login_at=now,
            )
        )
        user_id = int(result.inserted_primary_key[0])
        connection.commit()
        return user_id
    except IntegrityError as error:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An administrator already exists or the username is already taken.",
        ) from error
    finally:
        connection.close()


@router.get("/status")
def auth_status(db: Session = Depends(get_db)):
    has_users = db.query(User.id).first() is not None
    return {"setup_required": not has_users}


@router.post("/setup", status_code=status.HTTP_201_CREATED)
def setup_initial_admin(data: InitialAdminSetup, request: Request):
    user_id = _create_first_admin(data)
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The administrator account was created but could not be loaded.",
            )
        response = JSONResponse(
            {
                "user": UserResponse.model_validate(user).model_dump(mode="json"),
                "redirect_to": "/src/pages/dashboard.html",
            },
            status_code=status.HTTP_201_CREATED,
        )
        set_session_cookie(response, request, user.id)
        return response


@router.post("/login")
def login(data: LoginRequest, request: Request):
    client_key = _client_key(request)
    if _is_rate_limited(client_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed sign-in attempts. Wait five minutes and try again.",
        )

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == data.username).first()
        if user is None or not verify_password(data.password, user.password_hash):
            _record_failed_login(client_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )
        if not user.is_active:
            _record_failed_login(client_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        response = JSONResponse(
            {
                "user": UserResponse.model_validate(user).model_dump(mode="json"),
                "redirect_to": _safe_redirect_target(data.next),
            }
        )
        set_session_cookie(response, request, user.id)
        _clear_failed_logins(client_key)
        return response
    finally:
        db.close()


@router.post("/logout")
def logout():
    response = JSONResponse({"status": "logged_out"})
    clear_session_cookie(response)
    return response


@router.get("/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)):
    return user
