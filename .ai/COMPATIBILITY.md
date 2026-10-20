# Application / Database Compatibility

## Release 3.6.5
- Application version declaration: 3.6.5, selected by the user for the current develop-to-main promotion.
- Declared database schema range remains 1–11; latest migration remains 0011.
- No database schema change is introduced solely by the 3.6.5 version bump or the asset-message matching feature.
- Scan Result asset-match data is computed from live inventory when API responses are built. It does not add a table or column.
- Vulnerability Register custom fields require migration 0011, which adds custom_fields_json and the vulnerability_custom_fields definitions table. This migration belongs to the 3.5.0-era implementation; it is not a new 3.6.5 migration.
- Asset matches are advisory and must not be treated as proof of vulnerability applicability.
- Full upgrade, regression, browser and integration testing for 3.6.5 remains pending; see V3.6.5_RELEASE.md.

## Historical application/schema milestones
- 3.6.0: Scan Result asset-message matching first documented; schema remains 1–11; no migration required for matching.
- 3.5.0: Vulnerability Register custom fields; migration 0011; schema target 11.
- 3.4.0: Added users.must_change_password with migration 0010. Current bootstrap behavior is documented in STATE.md; older temporary-password behavior is historical and must not be assumed to describe current code.
- 3.3.0: Added local account table with migration 0009.
- 3.2.0: Added Nessus import, finding and host-mapping tables in migration 0008.

## Database
- Engine: SQLite.
- Default path: backend/data/vul_management.db.
- SQLAlchemy is the data-access layer; Alembic manages schema revisions.
- Never commit, delete, reset or replace the runtime database as a routine troubleshooting step.
- Before any migration or customer upgrade, identify the actual DB path and make a verified backup.
- Never edit a released migration in place; add a new migration for schema changes.
- Downgrading migration 0008 drops Nessus tables and deletes Nessus import data. Downgrading migrations 0009–0011 may remove accounts or custom-field data. Do not downgrade without a verified backup and explicit rollback plan.

## Verification commands
Run from backend with the project's virtual environment:
    alembic current
    alembic history
    alembic upgrade head
    python -m uvicorn app.main:app --reload

Verify the selected environment and database path before migrations. A successful startup alone does not prove migration safety, Nessus parsing, workflow correctness or overall production readiness.
