# Application / Database Compatibility

Application Version: 1.2.0
Minimum DB Schema: 1
Maximum DB Schema: 3

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
Adds feed synchronization metadata:
- last_sync_at
- last_sync_status
- last_sync_message

The application uses Alembic revisions as the database schema version.
Future schema changes require a new migration revision.

## Operational Commands

From backend:

alembic current
alembic history
alembic upgrade head

Do not edit released migration files.
