from fastapi import APIRouter, HTTPException

from app.schemas.threat_intelligence import (
    TelegramVerificationCodeRequest,
    TelegramVerificationSubmit,
)
from app.services.telegram_auth import (
    cancel_telegram_verification,
    get_telegram_status,
    send_telegram_verification_code,
    verify_telegram_code,
)

router = APIRouter(prefix="/api/administration/telegram", tags=["Administration - Telegram"])


@router.get("/status")
async def telegram_settings_status():
    return await get_telegram_status()


@router.post("/send-code")
async def telegram_send_verification_code(data: TelegramVerificationCodeRequest):
    try:
        return await send_telegram_verification_code(
            api_id=data.api_id,
            api_hash=data.api_hash,
            phone_number=data.phone_number,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        # Keep credentials and authentication codes out of API errors.
        raise HTTPException(
            status_code=400,
            detail=f"Could not request a Telegram verification code ({error.__class__.__name__}). Check the API credentials, phone number, and network connection.",
        ) from error


@router.post("/verify-code")
async def telegram_verify_code(data: TelegramVerificationSubmit):
    try:
        return await verify_telegram_code(
            challenge_id=data.challenge_id,
            code=data.code,
            password=data.password,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error



@router.delete("/verification/{challenge_id}")
async def telegram_cancel_verification(challenge_id: str):
    return await cancel_telegram_verification(challenge_id)
