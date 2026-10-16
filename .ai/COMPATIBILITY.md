# Application / Database Compatibility

## Current application identity
The shared frontend sidebar currently displays `v3.0.0`. This is a UI version label; verify the backend version and migration state directly before making compatibility claims.

## Database
- Engine: SQLite
- Default file: `backend/data/vul_management.db`
- Access layer: SQLAlchemy
- Schema versioning: Alembic
- The physical database file is local runtime state and is excluded from Git.

## Compatibility Window
Before a release or migration change, inspect:
- the actual Alembic revisions in `backend/alembic/versions/`,
- the current database revision using Alembic,
- the schema range enforced at application startup,
- the API/model changes required by the frontend.

Record the verified minimum and maximum supported schema revisions here. Do not copy schema numbers from old documentation without checking source.

## Migration policy
- Add a new Alembic revision for schema changes.
- Do not edit released migrations in place.
- Never delete/recreate the user's database as a routine way to fix a schema or application issue.
- Do not run destructive migrations against production data.
- Back up the database before any approved migration with potential data loss.
- The local DB must never be committed.

## Compatibility Window rule
A new application version should declare:
- application version/commit,
- minimum supported schema,
- maximum supported schema,
- required migration(s),
- whether migration is backward-compatible,
- any data transformation or data-loss risk,
- rollback/backup procedure.

Do not mark a release ready until the application/database compatibility has been checked and documented.

## Operational checks
From the backend working directory:
```powershell
alembic current
alembic history
alembic upgrade head
```

Run migration commands only after verifying the active virtual environment, database path and backup status. The command `alembic upgrade head` may change the schema; do not run it blindly against important data.
