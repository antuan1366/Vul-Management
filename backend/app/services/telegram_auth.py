from __future__ import annotations

import asyncio
import os
import secrets
import time
from pathlib import Path
from typing import Any

from app.core.config import settings

_PENDING: dict[str, dict[str, Any]] = {}
_PENDING_LOCK = asyncio.Lock()
CHALLENGE_TTL_SECONDS = 600


def _backend_env_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def _write_backend_env(values: dict[str, str]) -> None:
    """Persist local-only settings without returning secrets to the browser."""
    env_path = _backend_env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    found: set[str] = set()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in values:
            output.append(f"{key}={values[key]}")
            found.add(key)
        else:
            output.append(line)
    for key, value in values.items():
        if key not in found:
            output.append(f"{key}={value}")
    temporary = env_path.with_suffix(".env.tmp")
    temporary.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    temporary.replace(env_path)


def _apply_runtime_settings(api_id: str, api_hash: str, session_path: str) -> None:
    settings.telegram_api_id = api_id
    settings.telegram_api_hash = api_hash
    settings.telegram_session = session_path


def _new_client(api_id: str, api_hash: str, session_path: str):
    try:
        from telethon import TelegramClient
    except ImportError as error:
        raise RuntimeError("Telethon is not installed. Install the project requirements first.") from error
    path = Path(session_path)
    if not path.is_absolute():
        path = _backend_env_path().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return TelegramClient(str(path), int(api_id), api_hash)


async def get_telegram_status() -> dict:
    configured = bool(settings.telegram_api_id and settings.telegram_api_hash)
    result = {
        "configured": configured,
        "authorized": False,
        "pending_verification": bool(_PENDING),
        "api_id": settings.telegram_api_id or "",
        "session_path": settings.telegram_session,
        "phone_number": None,
    }
    if not configured:
        return result
    if _PENDING:
        result["pending_verification"] = True
        return result
    try:
        client = _new_client(settings.telegram_api_id, settings.telegram_api_hash, settings.telegram_session)
        await client.connect()
        try:
            result["authorized"] = bool(await client.is_user_authorized())
        finally:
            await client.disconnect()
    except Exception:
        result["authorized"] = False
    return result


async def send_telegram_verification_code(api_id: str, api_hash: str, phone_number: str) -> dict:
    api_id = (api_id or settings.telegram_api_id or "").strip()
    api_hash = (api_hash or settings.telegram_api_hash or "").strip()
    phone_number = phone_number.strip()
    if not api_id.isdigit():
        raise ValueError("API ID must contain digits only.")
    if not api_hash:
        raise ValueError("API Hash is required.")
    if not phone_number.startswith("+") or not phone_number[1:].replace(" ", "").isdigit():
        raise ValueError("Enter the phone number in international format, for example +374XXXXXXXX.")

    # Store credentials locally in backend/.env; the API never returns the hash.
    session_path = settings.telegram_session or "./data/telegram"
    _write_backend_env({
        "TELEGRAM_API_ID": api_id,
        "TELEGRAM_API_HASH": api_hash,
        "TELEGRAM_SESSION": session_path,
    })
    _apply_runtime_settings(api_id, api_hash, session_path)

    async with _PENDING_LOCK:
        for pending in list(_PENDING.values()):
            try:
                await pending["client"].disconnect()
            except Exception:
                pass
        _PENDING.clear()

        client = _new_client(api_id, api_hash, session_path)
        try:
            await client.connect()
            sent = await client.send_code_request(phone_number)
        except Exception:
            await client.disconnect()
            raise
        challenge_id = secrets.token_urlsafe(24)
        _PENDING[challenge_id] = {
            "client": client,
            "phone_number": phone_number,
            "phone_code_hash": sent.phone_code_hash,
            "created_at": time.time(),
        }
    return {
        "challenge_id": challenge_id,
        "phone_number": phone_number,
        "expires_in_seconds": CHALLENGE_TTL_SECONDS,
        "message": "Telegram sent a verification code. Enter it below to finish connecting.",
    }


async def verify_telegram_code(challenge_id: str, code: str, password: str | None = None) -> dict:
    pending = _PENDING.get(challenge_id)
    if pending is None:
        raise ValueError("Verification session not found. Send a new verification code.")
    if time.time() - pending["created_at"] > CHALLENGE_TTL_SECONDS:
        try:
            await pending["client"].disconnect()
        finally:
            _PENDING.pop(challenge_id, None)
        raise ValueError("Verification code session expired. Send a new verification code.")

    client = pending["client"]
    try:
        from telethon.errors import (
            PasswordHashInvalidError,
            PhoneCodeExpiredError,
            PhoneCodeInvalidError,
            SessionPasswordNeededError,
        )
        try:
            await client.sign_in(
                phone=pending["phone_number"],
                code=code.strip(),
                phone_code_hash=pending["phone_code_hash"],
            )
        except SessionPasswordNeededError:
            if not password:
                return {
                    "authorized": False,
                    "requires_2fa": True,
                    "message": "This Telegram account has two-step verification enabled. Enter its Telegram password.",
                }
            try:
                await client.sign_in(password=password)
            except PasswordHashInvalidError as error:
                raise ValueError("The Telegram two-step verification password is incorrect.") from error
        except PhoneCodeInvalidError as error:
            raise ValueError("The verification code is incorrect. Check it and try again.") from error
        except PhoneCodeExpiredError as error:
            raise ValueError("The verification code expired. Send a new code.") from error

        if not await client.is_user_authorized():
            return {
                "authorized": False,
                "requires_2fa": False,
                "message": "Telegram has not authorized this session yet.",
            }
        await client.disconnect()
        _PENDING.pop(challenge_id, None)
        return {
            "authorized": True,
            "requires_2fa": False,
            "message": "Telegram account connected successfully. The local session is ready for scans.",
        }
    except ValueError:
        raise
    except Exception as error:
        # Do not include submitted codes, passwords, or credentials in errors/logs.
        raise ValueError(f"Telegram verification failed ({error.__class__.__name__}). Check the code or request a new one.") from error



async def cancel_telegram_verification(challenge_id: str) -> dict:
    async with _PENDING_LOCK:
        pending = _PENDING.pop(challenge_id, None)
        if pending:
            try:
                await pending["client"].disconnect()
            except Exception:
                pass
    return {"cancelled": True}
