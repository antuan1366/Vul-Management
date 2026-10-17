# Application / Database Compatibility

## Release 3.1.0
- Branch: `develop`
- Application version: `3.1.0`
- Migration: `0008`, revises `0007`
- Declared supported schema range: `1–8`
- Migration intent: additive; creates `nessus_imports`, `nessus_findings`, and `nessus_host_mappings`.
- No existing tables are intentionally dropped or transformed during upgrade.
- Downgrade 0008 drops these three tables and deletes Nessus import data. Back up the database first and do not downgrade after importing reports unless that data is disposable.

## Database
- SQLite default: `backend/data/vul_management.db`
- SQLAlchemy is the data-access layer; Alembic manages schema revisions.
- Never commit, delete, or replace the runtime database.

## Checks (not yet run)
From `backend`, after installing requirements:
```powershell
alembic current
alembic history
alembic upgrade head
python -m uvicorn app.main:app --reload
```
Verify the active environment and database path before migration. The source change is not runtime-verified; validate with a synthetic fixture and a real Nessus export before release sign-off.
