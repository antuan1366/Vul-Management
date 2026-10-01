# Application / Database Compatibility

## Purpose

This document defines the compatibility policy between the Vul-Management
application version and database schema version.

The application version and database schema version are independent.

The database must be able to evolve through forward migrations while allowing
a defined compatibility window for supported application versions.

## Core Rules

1. Application version and database schema version are independent.
2. Database schema changes are managed through versioned migrations.
3. Applied migrations must never be edited after they have been released.
4. Database migrations are forward-only for normal upgrades.
5. An application release must declare its supported database schema window.
6. An application must refuse to start when the database schema is outside its
   supported window.
7. A database schema newer than the application's maximum supported schema must
   never be used silently by an older application.
8. Application rollback should not require database rollback when the previous
   application version remains inside the database compatibility window.
9. Breaking database changes require a new compatibility boundary and must be
   introduced through an explicit migration/release strategy.
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

the following is expected:

- DB 3: incompatible; migration required
- DB 4: compatible
- DB 5: compatible
- DB 6: incompatible; database is newer than the application

## Backward-Compatible Database Changes

New schema changes should, whenever practical, be introduced in a way that
allows the previous application release to continue operating.

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

If App 1.4.x must be rolled back, App 1.3.x can be restored while DB Schema 5
remains in place, provided App 1.3.x declares DB Schema 5 as compatible.

Database restoration should be considered separately when a schema change is
destructive or outside the previous application's compatibility window.

## Database Version Tracking

The future migration system will maintain the current database schema version
inside the database.

The migration tool will be the source of truth for applied schema changes.

The application will use its release metadata to validate the database version
at startup.

The intended runtime flow is:

```
Application starts
       |
       v
Read application compatibility metadata
       |
       v
Read current DB schema version
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

## Release Metadata

Every release should eventually define compatibility similar to:

```text
Application Version: 1.4.0
Minimum DB Schema:   4
Maximum DB Schema:   5
```

This information must exist in the application release itself for runtime
validation. This document remains the project-level compatibility reference
for developers, release management, and AI-assisted development.

## Current Project Status

The current project still uses an unversioned SQLite schema and contains an
older startup migration for the Equipment name column.

Before the first formal schema-versioned release:

1. Introduce Alembic.
2. Create a baseline migration for the existing schema.
3. Move future schema changes out of `database.py`.
4. Add DB schema version validation at application startup.
5. Define compatibility windows for each release.
6. Test upgrade and application rollback scenarios.

Until this migration system is introduced, no formal DB schema compatibility
number should be considered authoritative.

## Planned Migration Architecture

```
backend/
├── app/
│   ├── core/
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── database.py
│
└── alembic/
    ├── versions/
    └── env.py
```

Alembic will manage schema migrations.

The application version will remain independent from Alembic's migration
revision.

## Important Constraint

`.ai/COMPATIBILITY.md` is the project-level documentation and planning
reference. It is not the runtime authority.

Runtime compatibility must be enforced by release metadata and the database's
actual schema version.

Changes to compatibility rules must be reviewed as part of the corresponding
release.
