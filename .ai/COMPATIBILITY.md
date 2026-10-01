# Application / Database Compatibility

## Purpose

This document defines the compatibility policy between the Vul-Management
application version and database schema version.

The application version and database schema version are independent.

The database evolves through forward migrations while each application release
supports a defined database compatibility window.

## Core Rules

1. Application version and database schema version are independent.
2. Database schema changes are managed through versioned Alembic migrations.
3. Applied migrations must never be edited after release.
4. Database upgrades are forward-only for normal releases.
5. Each application release declares a minimum and maximum supported DB schema.
6. The application refuses to start when the DB schema is outside that window.
7. A database schema newer than the application's maximum supported schema must
   never be used silently by an older application.
8. Application rollback should not require database rollback when the previous
   application version remains inside the compatibility window.
9. Breaking database changes require a new compatibility boundary.
10. Database backups are separate from Git and must not be stored in the
    repository.

## Current Release

Application Version: 1.0.0
Minimum DB Schema: 1
Maximum DB Schema: 1

The current 1.0.0 release is compatible with Alembic schema revision 0001.

## Current Runtime Implementation

The project has the first formal database-versioning foundation:

- Alembic is installed as a project dependency.
- backend/alembic/ contains the migration environment.
- 0001 is the baseline schema revision.
- backend/app/core/database_version.py reads the current Alembic revision.
- Application startup validates the database against the configured
  compatibility window.
- Application version remains independent from DB schema version.

Runtime configuration currently uses:

DB_SCHEMA_MIN=1
DB_SCHEMA_MAX=1

These values can be overridden through the normal application settings
environment.

## Baseline Transition

The project previously used SQLAlchemy create_all() and a small startup
migration for the Equipment name column.

During this transition:

1. The existing legacy Equipment migration still runs.
2. SQLAlchemy creates missing current tables.
3. If the database has no alembic_version table, it is stamped at the
   current Alembic head.
4. The application reads the resulting Alembic revision.
5. The compatibility window is validated.

This prevents existing development databases from being treated as brand-new
databases.

Future schema changes must not be added as new startup migration functions.

## Backward-Compatible Database Changes

New schema changes should, whenever practical, be introduced so that the
previous application release can continue operating.

Preferred sequence:

1. Add new database structure without removing old structure.
2. Deploy application code that can work with both old and new structure.
3. Start using the new structure.
4. Remove obsolete structure only after the compatibility window no longer
   requires the old application.

This is the preferred strategy for safe application rollback.

## Application Rollback

Application rollback does not automatically imply database rollback.

A previous application version may be run against the current database only
when its declared compatibility window includes the current database schema.

Database restoration is a separate operational decision for destructive
changes or databases outside the previous application's compatibility window.

## Database Version Tracking

Alembic maintains the current database revision in the database's
alembic_version table.

Migration revision IDs are numeric in this project:

0001
0002
0003
...

The numeric revision is the project DB schema version.

## Migration Commands

From the backend directory:

alembic current
alembic history
alembic upgrade head

For a new schema change:

alembic revision -m "describe schema change"

The generated migration must be reviewed and tested before it becomes part
of a release.

## Important Constraint

.ai/COMPATIBILITY.md is documentation and policy, not the runtime source
of truth.

Runtime compatibility is enforced by the application's release configuration
and the database's actual Alembic revision.

Any compatibility-window change must be reviewed as part of the corresponding
application release.


## Revision 0002

Revision 0002 adds:

- Feed configuration
- Security identifiers
- Vulnerability inventory
- Asset/Vulnerability mappings

Existing schema revision 0001 databases are upgraded automatically to 0002 at application startup.
