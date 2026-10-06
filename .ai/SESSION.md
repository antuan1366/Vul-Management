# SESSION

## Current Session

The project is being prepared for the 2.0.0 major release candidate.

The user requested a file-based database and then clarified the Vulnerabilities workflow: scanning must have an in-page status/control window, scans must be schedulable by day/time, the old standalone Sync Status and NVD Days Back controls must be removed, and each finding must carry an actionable administrator review state.

Git inspection confirmed that the application already uses SQLite, so the work remains formalized around the SQLite single-file architecture.

## Current Branch

feature/v2-sqlite-foundation

Based on:

feature/approved-findings-sync-status

No changes have been merged to main.

## Current Database

SQLite

Default file:

backend/data/vul_management.db

The database file is excluded from Git.

SQLAlchemy remains the data-access layer and Alembic remains the schema versioning mechanism.

## Current Application Version

2.0.0 release candidate

Supported database schema:
1-5

## Current Vulnerability UX

The Vulnerabilities page is now the single control point for discovery and review.

Discovery status shows:
- Last Scan
- Next Scan
- Scan Status
- Pending Review count

Controls:
- Daily scan enable/disable
- Daily scan time
- Save Schedule
- Scan Now
- CISA KEV update

Findings are shown in one table with:
- CVE
- Asset
- Severity
- CVSS
- Applicability
- Status
- CISA KEV
- Admin actions

Finding states:
- Pending Review
- Approved
- Rejected

A newly discovered candidate starts as Pending Review. Approval creates/updates the approved vulnerability and its asset mapping. Rejection remains visible as Rejected until a future discovery updates the candidate.

The standalone Sync Status page has been removed. NVD Days Back is no longer exposed in the Vulnerabilities UI.

## Scan Scheduling

A persistent scan_schedules table stores the daily schedule and last/next scan metadata.

The FastAPI lifespan starts a lightweight scheduler loop. It checks the persisted schedule and starts an NVD discovery job when the configured daily time is reached.

The scheduler is intentionally disabled by default.

## Git Workflow

1. Develop on feature branches.
2. Test locally.
3. Review API/UI.
4. Update .ai documentation.
5. User approves.
6. Create/prepare Pull Request.
7. User reviews Pull Request.
8. User performs the merge.
9. Tag the release when appropriate.

Do not merge Pull Requests automatically.

## Important

The 2.0.0 label is a release-candidate target, not permission to merge.

The next action after this documentation update is local testing.

## AI Scope

AI/Mem0/Gemini remains postponed.

The core application must operate without AI.
