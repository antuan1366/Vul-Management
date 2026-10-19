# Customer Deployment and Clean Data

## Purpose

Build a customer ZIP from the current source tree without copying developer-specific runtime data. The ZIP contains application source and a fresh `backend/.env` generated from `backend/.env.example`; it does not use the developer's real `.env`.

The application creates its SQLite database and initial baseline records on first startup. Subsequent startups reuse that database and apply the existing database-version/migration mechanism. Do not delete the customer's data directory when upgrading.

## Build the ZIP

From the repository root, run:

```powershell
python scripts/build_customer_package.py
```

Output:

```text
dist/Vul-Management-customer.zip
```

The builder excludes Git metadata, internal `.ai` notes, virtual environments, runtime data directories, local `.env` files and backups, SQLite files, logs, Python cache files, and Telegram session files. It also refuses to build if known credential fields in `backend/.env.example` contain non-empty values.

Review the generated archive before delivering it. This script is a packaging safeguard, not a complete security audit or installer.

## Install on a Windows customer machine

1. Extract the ZIP to a customer-owned application directory, for example `C:\\Vul-Management`.
2. Open PowerShell in the extracted `backend` directory.
3. Create a virtual environment and install the dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

4. Edit `backend/.env` locally if the customer needs Telegram or Jira integration. Do not send credentials to the developer or commit this file.
5. Keep `DATA_DIR=./data` and `DATABASE_URL=` to use the default data folder, or set `DATA_DIR` to an absolute customer-owned directory such as `E:/Vul-Management-Data`. Leave `DATABASE_URL` blank unless an explicit SQLAlchemy database URL is required.
6. Leave `TELEGRAM_SESSION=` blank to let the application use `DATA_DIR/telegram`. Configure the customer's own Telegram API credentials only if that integration is required. Never copy a developer's `.session` file into the customer installation.
7. Start the application from the `backend` directory:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

8. Open `http://127.0.0.1:8000`.

The first startup creates the database and seeds the application's baseline records, including configured public/default feeds. Customer assets, findings, scans, and later configuration are stored in that customer's data directory.

## Important safeguards

- Never package the developer's real `.env`, database, Telegram session, Jira token, or logs.
- Do not reuse a customer's data directory for another customer.
- Back up the customer's data directory before upgrades or migration work.
- Do not delete or recreate the database on each startup.
- The command above binds to localhost. Do not expose the application to a LAN or the internet unless authentication, access controls, HTTPS/reverse proxy configuration, and a security review are in place.
- The builder does not automatically package Python itself or install dependencies; the customer machine needs a supported Python version and network access to install requirements, or a separately prepared offline dependency bundle.
- Validate the ZIP and perform a clean-install smoke test before any production delivery.
