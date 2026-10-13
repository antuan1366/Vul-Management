"""Run from the backend directory to create the local Telethon session file.

Set TELEGRAM_API_ID and TELEGRAM_API_HASH in the environment first.
The session file contains account access and must never be committed.
"""
import asyncio
import os
from pathlib import Path

from telethon import TelegramClient


def load_local_env() -> None:
    env_file = Path(".env")
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\\\"").strip("\\'"))


async def main() -> None:
    load_local_env()
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
