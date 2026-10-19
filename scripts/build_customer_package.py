#!/usr/bin/env python3
"""Build a customer ZIP without local databases, credentials, or Telegram sessions.

Run from any directory:
    python scripts/build_customer_package.py

The generated archive is written to dist/Vul-Management-customer.zip.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "Vul-Management-customer.zip"
ENV_EXAMPLE = ROOT / "backend" / ".env.example"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".ai",  # internal project notes
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}
SENSITIVE_TEMPLATE_KEYS = {
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
    "JIRA_BASE_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_PROJECT_KEY",
}


def is_runtime_data_dir(relative_path: Path) -> bool:
    normalized = relative_path.as_posix().strip("/")
    return normalized in {"data", "backend/data"}


def should_exclude(relative_path: Path) -> bool:
    parts = relative_path.parts
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    if is_runtime_data_dir(relative_path):
        return True

    name = relative_path.name
    if name != ".env.example" and (name == ".env" or name.startswith(".env.")):
        return True
    if name.endswith((".db", ".sqlite", ".sqlite3", ".log", ".session", ".session-journal", ".pyc", ".pyo", ".tmp", ".temp")):
        return True
    return False


def validate_env_template(text: str) -> None:
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() in SENSITIVE_TEMPLATE_KEYS and value.strip():
            raise ValueError(
                f"Refusing to package: backend/.env.example has a non-empty "
                f"{key.strip()} value on line {line_number}."
            )


def main() -> int:
    if not ENV_EXAMPLE.is_file():
        print(f"Required template not found: {ENV_EXAMPLE}", file=sys.stderr)
        return 2

    env_template = ENV_EXAMPLE.read_text(encoding="utf-8")
    try:
        validate_env_template(env_template)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    included: list[str] = []
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if should_exclude(relative):
                continue

            archive_name = (Path("Vul-Management") / relative).as_posix()
            archive.write(path, archive_name)
            included.append(archive_name)

        # Never package the developer's real .env. Generate a clean customer
        # .env from the reviewed template instead.
        generated_env_name = "Vul-Management/backend/.env"
        archive.writestr(generated_env_name, env_template)
        included.append(generated_env_name)

    # Verify the final archive itself, not only the file-copy decisions.
    with zipfile.ZipFile(OUTPUT, "r") as archive:
        names = archive.namelist()
        forbidden = []
        for name in names:
            relative = Path(name).relative_to("Vul-Management")
            if should_exclude(relative):
                forbidden.append(name)
        if forbidden:
            OUTPUT.unlink(missing_ok=True)
            print("Package validation failed; excluded artifacts found:", file=sys.stderr)
            print("\n".join(forbidden), file=sys.stderr)
            return 3
        if "Vul-Management/backend/.env" not in names:
            OUTPUT.unlink(missing_ok=True)
            print("Package validation failed: generated backend/.env is missing.", file=sys.stderr)
            return 3

    print(f"Customer package created: {OUTPUT}")
    print(f"Files included: {len(included)}")
    print("Excluded: local .env files, databases, runtime data folders, logs, and Telegram sessions.")
    print("The bundled backend/.env is generated from backend/.env.example; review that template before release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
