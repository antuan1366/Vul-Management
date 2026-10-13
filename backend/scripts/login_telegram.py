"""Run from the backend directory to create the local Telethon session file.

Set TELEGRAM_API_ID and TELEGRAM_API_HASH in the environment first.
The session file contains account access and must never be committed.
"""
import asyncio
import os
from pathlib import Path

from telethon import TelegramClient


async def main() -> None:
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_path = os.getenv("TELEGRAM_SESSION", "./data/telegram")
    if not api_id or not api_hash:
        raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH before login.")

    Path(session_path).parent.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(session_path, int(api_id), api_hash)
    await client.start()
    print("Telegram login successful. Keep the session file private and out of Git.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
