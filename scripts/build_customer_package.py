#!/usr/bin/env python3
"""Build a customer ZIP without local databases, credentials, or Telegram sessions.

Run from the repository root (or any directory):
    python scripts/build_customer_package.py

Only committed/tracked source files are eligible for packaging. The generated
archive is written to dist/Vul-Management-customer.zip.
"""
from __future__ import annotations

import subprocess
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
SENSITIVE_FILE_NAMES = {
    "credentials.json",
    "secrets.json",
    "token.json",
    "id_rsa",
    "id_ed25519",
}
SENSITIVE_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".log",
    ".session",
    ".session-journal",
    ".pyc",
    ".pyo",
    ".tmp",
    ".temp",
    ".bak",
    ".backup",
    ".pem",
    ".p12",
    ".pfx",
    ".key",
}


def is_runtime_data_dir(relative_path: Path) -> bool:
    normalized = relative_path.as_posix().strip("/").lower()
    return (
        normalized in {"data", "backend/data"}
        or normalized.startswith("data/")
        or normalized.startswith("backend/data/")
    )


def should_exclude(relative_path: Path) -> bool:
    parts = {part.lower() for part in relative_path.parts}
    if parts.intersection(EXCLUDED_DIR_NAMES):
        return True
    if is_runtime_data_dir(relative_path):
        return True

    name = relative_path.name.lower()
    if name != ".env.example" and (name == ".env" or name.startswith(".env.")):
        return True
    if name in SENSITIVE_FILE_NAMES:
        return True
    if name.endswith(("-wal", "-shm", ".session-journal")):
        return True
    if name.endswith(tuple(SENSITIVE_SUFFIXES)):
        return True
    return False


def validate_env_template(text: str) -> None:
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip().upper() in SENSITIVE_TEMPLATE_KEYS and value.strip():
            raise ValueError(
                f"Refusing to package: backend/.env.example has a non-empty "
                f"{key.strip()} value on line {line_number}."
            )


def tracked_source_files() -> list[Path]:
    """Return committed Git-tracked files; never sweep arbitrary local files."""
    status = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0:
        raise RuntimeError("Unable to inspect Git status. Build from a Git checkout.")

    if status.stdout.strip():
        raise RuntimeError(
            "Tracked files have local modifications. Commit or revert them before "
            "building a customer package, then run the builder again."
        )

    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Unable to list Git-tracked files.")

    paths = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(raw_path.decode("utf-8"))
        full_path = ROOT / relative
        if full_path.is_file() and not full_path.is_symlink() and not should_exclude(relative):
            paths.append(full_path)
    return sorted(paths)


def main() -> int:
    if not ENV_EXAMPLE.is_file():
        print(f"Required template not found: {ENV_EXAMPLE}", file=sys.stderr)
        return 2

    env_template = ENV_EXAMPLE.read_text(encoding="utf-8")
    try:
        validate_env_template(env_template)
        files = tracked_source_files()
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    generated_env_name = "Vul-Management/backend/.env"
    included: list[str] = []
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(ROOT)
            archive_name = (Path("Vul-Management") / relative).as_posix()
            archive.write(path, archive_name)
            included.append(archive_name)

        # Generate a clean customer environment file instead of copying .env.
        archive.writestr(generated_env_name, env_template)
        included.append(generated_env_name)

    # Independently verify the actual archive entries and generated environment.
    with zipfile.ZipFile(OUTPUT, "r") as archive:
        names = archive.namelist()
        forbidden = []
        for name in names:
            relative = Path(name).relative_to("Vul-Management")
            if relative.as_posix() == "backend/.env":
                continue
            if should_exclude(relative):
                forbidden.append(name)

        if len(names) != len(set(names)):
            forbidden.append("<duplicate archive paths>")
        if forbidden:
            OUTPUT.unlink(missing_ok=True)
            print("Package validation failed; excluded artifacts found:", file=sys.stderr)
            print("\n".join(forbidden), file=sys.stderr)
            return 3
        if generated_env_name not in names:
            OUTPUT.unlink(missing_ok=True)
            print("Package validation failed: generated backend/.env is missing.", file=sys.stderr)
            return 3
        if archive.read(generated_env_name).decode("utf-8") != env_template:
            OUTPUT.unlink(missing_ok=True)
            print("Package validation failed: generated backend/.env did not match the reviewed template.", file=sys.stderr)
            return 3

    print(f"Customer package created: {OUTPUT}")
    print(f"Files included: {len(included)}")
    print("Source files: committed Git-tracked files only; tracked working-tree changes block packaging.")
    print("Excluded: local .env files, databases, runtime data, logs, Telegram sessions, private-key files, and build caches.")
    print("The bundled backend/.env is generated from backend/.env.example; review that template before release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
