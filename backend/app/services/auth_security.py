import base64
import hashlib
import hmac
import os
import secrets
import threading

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import settings


SESSION_COOKIE_NAME = "vul_management_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
PBKDF2_ITERATIONS = 600_000
_PASSWORD_HASH_SCHEME = "pbkdf2_sha256"

_serializer = None
_serializer_lock = threading.Lock()


def _get_serializer() -> URLSafeTimedSerializer:
    global _serializer
    if _serializer is not None:
        return _serializer

    with _serializer_lock:
        if _serializer is not None:
            return _serializer

        secret = settings.session_secret
        if not secret:
            settings.data_dir.mkdir(parents=True, exist_ok=True)
            secret_path = settings.data_dir / "session-signing.key"
            try:
                with secret_path.open("x", encoding="utf-8") as secret_file:
                    secret_file.write(secrets.token_urlsafe(48))
            except FileExistsError:
                pass

            secret = secret_path.read_text(encoding="utf-8").strip()
            try:
                os.chmod(secret_path, 0o600)
            except OSError:
                # Windows does not support POSIX permission modes.
                pass

        if not secret or len(secret) < 32:
            raise RuntimeError(
                "VULM_SESSION_SECRET must contain at least 32 characters."
            )

        _serializer = URLSafeTimedSerializer(secret, salt="vul-management-session-v1")
        return _serializer


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=32,
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    key_text = base64.urlsafe_b64encode(derived_key).decode("ascii")
    return (
        _PASSWORD_HASH_SCHEME + "$" + str(PBKDF2_ITERATIONS) + "$"
        + salt_text + "$" + key_text
    )


def verify_password(password: str, encoded_hash: str | None) -> bool:
    if not password or not encoded_hash:
        return False

    try:
        scheme, rounds_text, salt_text, expected_text = encoded_hash.split("$", 3)
        if scheme != _PASSWORD_HASH_SCHEME:
            return False
        rounds = int(rounds_text)
        if rounds < 100_000 or rounds > 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            rounds,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def create_session_token(user_id: int) -> str:
    return _get_serializer().dumps({"uid": int(user_id)})


def get_session_user_id(token: str | None) -> int | None:
    if not token:
        return None

    try:
        payload = _get_serializer().loads(token, max_age=SESSION_TTL_SECONDS)
        user_id = int(payload.get("uid"))
        return user_id if user_id > 0 else None
    except (BadSignature, SignatureExpired, TypeError, ValueError, AttributeError):
        return None
