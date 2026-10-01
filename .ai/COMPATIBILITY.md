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

## Compatibility Window

Each application release has:

- Minimum supported DB schema
- Maximum supported DB schema

Example:

| Application | Minimum DB | Maximum DB |
|---|---:|---:|
| 1.2.x | 2 | 3 |
| 1.3.x | 3 | 4 |
| 1.4.x | 4 | 5 |

For an application release with:

- Minimum DB = 4
- Maximum DB = 5

the expected behavior is:

- DB 3: incompatible; migration required
- DB 4: compatible
- DB 5: compatible
- DB 6: incompatible; database is newer than the application

## Current Runtime Implementation

The project now has the first formal database-versioning foundation:

- Alembic is installed as a project dependency.
- `backend/alembic/` contains the migration environment.
- `0001` is the baseline schema revision.
- `backend/app/core/database_version.py` reads the current Alembic revision.
- Application startup validates the database against the configured
  compatibility window.
- Application version remains independent from DB schema version.
- The current application version `0.1.1` supports DB schema `1` only.

Runtime configuration currently uses:

```text
DB_SCHEMA_MIN=1
DB_SCHEMA_MAX=1
```

These values can be overridden through the normal application settings
environment.

## Baseline Transition

The current project previously used SQLAlchemy `create_all()` and a small
startup migration for the Equipment name column.

During this transition:

1. The existing legacy Equipment migration still runs.
2. SQLAlchemy creates missing current tables.
3. If the database has no `alembic_version` table, it is stamped at the
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

Example:

```
DB Schema 5
   |
   +-- App 1.3.x  -> compatible
   |
   +-- App 1.4.x  -> compatible
```

If App 1.4.x must be rolled back, App 1.3.x can remain on DB Schema 5 when
its compatibility window includes schema 5.

Database restoration is a separate operational decision for destructive
changes or databases outside the previous application's compatibility window.

## Database Version Tracking

Alembic maintains the current database revision in the database's
`alembic_version` table.

Migration revision IDs are numeric in this project:

```text
0001
0002
0003
...
```

The numeric revision is the project DB schema version.

Application startup performs:

```
Application starts
       |
       v
Read application compatibility window
       |
       v
Read current Alembic revision
       |
       v
Check Min DB <= Current DB <= Max DB
       |
   +---+---+
   |       |
  YES      NO
   |       |
   v       v
Start    Stop with clear
App      compatibility error
```

## Migration Commands

From the `backend` directory:

```powershell
alembic current
alembic history
alembic upgrade head
```

For a new schema change:

```powershell
alembic revision -m "describe schema change"
```

The generated migration must be reviewed and tested before it becomes part
of a release.

## Release Metadata

Every release should eventually define compatibility similar to:

```text
Application Version: 1.4.0
Minimum DB Schema:   4
Maximum DB Schema:   5
```

The runtime values belong to the application release. This document remains
the project-level compatibility reference for developers, release management,
and AI-assisted development.

## Important Constraint

`.ai/COMPATIBILITY.md` is documentation and policy, not the runtime source
of truth.

Runtime compatibility is enforced by the application's release configuration
and the database's actual Alembic revision.

Any compatibility-window change must be reviewed as part of the corresponding
application release.
