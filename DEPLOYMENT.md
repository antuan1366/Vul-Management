# Customer Deployment Preparation

This document is a deployment checklist for Vul-Management 3.2.0, not a claim that a production installer has been completed or certified.

## Current verification level

The developer reports that the application starts locally and that Asset Management, Nessus Manual Scan, Nessus Scan Results, Threat Intelligence, Administration, and Logs & Events open successfully. The following are still release gates:
- Nessus upload and parsing, finding review, CVE promotion/deduplication, and host mapping.
- Telegram scanning and NVD enrichment.
- Jira issue creation against a test project.
- Fresh database initialization and migration/upgrade testing.
- Installation on a separate clean Windows machine.

## Important security gate

Do not expose this build to an untrusted network or treat it as production-ready until the security configuration has been reviewed. In the current source inspected for this checklist:
- `debug` defaults to `True`.
- CORS is configured with `allow_origins=["*"]`.
- The main application module does not show authentication middleware. Confirm whether authentication and authorization exist elsewhere before deployment.

The environment template sets `DEBUG=false`, but the CORS policy and access-control design require a code-level review. Do not rely on hiding the URL as access control.

## Source preparation

1. Obtain the reviewed release source from the intended Git branch/tag.
2. Do not include the developer's `.venv`, `backend/data/`, `backend/.env`, logs, cache files, or Telegram `.session` files.
3. Keep `backend/.env.example` as a template. Copy it to `backend/.env` on the target machine and insert only that customer's own configuration.
4. Never put API tokens, passwords, private session files, or real customer data into Git or the package.
5. Dependencies in `backend/requirements.txt` currently use version ranges rather than a fully pinned lock file. Generate and test a reproducible dependency lock before distributing a production package.

## Windows setup for a controlled test machine

Use a separate test folder and a supported Python version chosen after dependency validation. From PowerShell:

```powershell
# Extract the clean source archive into a new folder first.
cd C:\Vul-Management\backend

# Create a new isolated environment.
py -3 -m venv ..\.venv

# Install dependencies into that environment.
..\.venv\Scripts\python.exe -m pip install --upgrade pip
..\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Copy backend\.env.example to backend\.env and configure it before starting.
# Start the app from the backend directory so the default relative SQLite path is consistent.
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

This bind address is for local testing only. Do not change it to `0.0.0.0` until authentication, CORS, firewall, TLS/reverse proxy, and deployment requirements are reviewed.

Open `http://127.0.0.1:8000/api/info` and confirm the reported app version and schema range. Also check the terminal for startup/migration errors.

## Database backup and restore

- Stop the application before taking a simple file-level SQLite backup, or use SQLite's supported backup mechanism while it is running.
- Preserve the whole database file and record the application version and schema revision with the backup.
- Test restoring a copy before relying on the backup.
- Never test migrations or downgrade operations against the only copy of customer data.
- Migration 0008 downgrade removes Nessus tables and their imported data; avoid downgrade as a routine rollback plan.

## Release acceptance checklist

- [ ] Security review: authentication, authorization, CORS, debug mode, secrets, upload limits, and network exposure.
- [ ] Reproducible dependency lock created and tested.
- [ ] Fresh database starts successfully on a clean machine.
- [ ] Existing database upgrade succeeds on a copy and data integrity is checked.
- [ ] Nessus end-to-end workflow passes with a synthetic report.
- [ ] Telegram/NVD workflow passes with controlled test data.
- [ ] Jira integration passes against a non-production project.
- [ ] Backup and restore have been tested.
- [ ] Clean package excludes databases, secrets, virtual environments, logs, and Telegram sessions.
- [ ] Installation/start/stop/upgrade steps have been followed by someone other than the developer.
- [ ] Only then create an immutable version tag and customer release archive.
