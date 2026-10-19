# STATE

## Snapshot
- Project: Vul-Management
- Version declaration: 3.2.0
- Active development branch: `develop`
- Declared schema range: 1–8
- Latest known migration: 0008
- Backend and sidebar version declarations were updated to 3.2.0.

## User-reported verification
Local app startup succeeded. The user reports page-level smoke tests passed for:
- Asset Management
- Nessus Manual Scan
- Nessus Scan Results
- Threat Intelligence
- Administration
- Logs & Events

This confirms basic navigation/page rendering only. The following remain unverified unless separately tested: database migration on a clean database, Nessus upload and parsing, finding review transitions, register deduplication, host mapping, Telegram scan/enrichment, Jira issue creation, and deployment on a clean machine.

## Existing platform
- FastAPI, SQLAlchemy, Alembic, SQLite, plain HTML/CSS/JavaScript.
- Asset inventory for Equipment, Operating Systems, Applications, and Libraries.
- Telegram-based threat-intelligence workflow and shared vulnerability register.
- Nessus import/finding tables and host-mapping workflow in source.
- Runtime database default: `backend/data/vul_management.db`.

## Next steps
1. Complete end-to-end feature checks using non-production test data.
2. Validate Alembic migration and schema compatibility against a backed-up test DB.
3. Create a deployment package that excludes local database, secrets, virtual environment, and cache files.
4. Install and test the package on a separate clean Windows machine.
5. Create a version tag/release only after final release verification and approval.

## Safety
Do not delete or replace local runtime data. Do not claim tests passed unless the user or an automated test actually confirmed them.
