# Application / Database Compatibility

## Release 3.3.0 (in development on develop)
- Application version declaration: 3.3.0.
- Declared database schema range: 1–9; latest migration: 0009.
- Migration 0009 adds the users table for local accounts, roles, password hashes, account status and last-login timestamps.
- Existing databases must be backed up and upgraded through Alembic before local runtime testing. Migration/runtime execution has not yet been verified after this change.
- A generated signing key is stored in backend/data/session-signing.key when VULM_SESSION_SECRET is not configured. Retain this file to preserve existing signed sessions across restarts; losing it invalidates sessions but does not delete user accounts.
- Downgrading migration 0009 drops the users table and all local account records. Do not downgrade unless a verified database backup exists and the resulting access loss is understood.

## Release 3.2.0
- Application version declarations: `3.2.0` (backend API and sidebar).
- Declared Alembic schema range: `1–8`; latest known migration: `0008`.
- Migration 0008 adds the Nessus import, finding, and host-mapping tables.
- No migration was performed as part of this documentation update.
- The user's local smoke test reports the app starts and page-level checks pass. Full migration/upgrade and Nessus XML workflow testing remain unconfirmed.

## Database
- SQLite default path: `backend/data/vul_management.db`.
- SQLAlchemy is the data-access layer; Alembic manages schema revisions.
- Never commit, delete, reset, or replace the runtime database as a routine troubleshooting step.
- Before any migration or customer upgrade, identify the actual DB path and make a verified backup.
- Downgrading migration 0008 drops Nessus tables and deletes Nessus import data; do not downgrade unless that data is disposable and a backup exists.

## Verification commands
Run from `backend` with the project's virtual environment active:
```powershell
alembic current
alembic history
alembic upgrade head
python -m uvicorn app.main:app --reload
```
Verify the selected environment and database path before running migrations. A successful startup alone does not prove a database upgrade, real Nessus report parsing, or every workflow is correct.
