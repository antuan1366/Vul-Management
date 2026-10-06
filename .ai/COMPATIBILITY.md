# Application / Database Compatibility

## Current Release Candidate

Application Version: 2.0.0
Minimum DB Schema: 1
Maximum DB Schema: 5

## Database Engine

Current engine: SQLite

Default file:

backend/data/vul_management.db

The physical database file is local state and is not committed to Git.

## Revisions

### 0001
Baseline application schema.

### 0002
Adds:
- feeds
- security_identifiers
- vulnerabilities
- asset_vulnerabilities

### 0003
Adds:
- last_sync_at
- last_sync_status
- last_sync_message

### 0004
Adds:
- vulnerability_candidates
- sync_jobs
- candidate review workflow
- synchronization job tracking

Migration 0004 intentionally resets the current development/test data while
upgrading the development database. Default fields and feeds are re-seeded
by application startup.

This destructive reset is a development-only decision and must not be
reused for production migrations.

### 0005
Adds:
- scan_schedules
- persistent daily vulnerability scan configuration
- last/next scan metadata

The scheduler is disabled by default.

## Compatibility Policy

The application validates the supported database schema range at startup.

Future schema changes require a new Alembic revision.

Released migrations must not be edited after release.

Major-version upgrades may intentionally change the supported schema window.

## Operational Commands

From backend:

alembic current
alembic history
alembic upgrade head

For a clean development database, remove the local SQLite file and allow
the application bootstrap/migrations to recreate it.

For production, use an explicit backup and migration procedure. Never delete
the production database to solve a schema problem.
