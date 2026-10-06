# SESSION

## Current Session

The project is being prepared for the 2.0.0 major release candidate.

The user requested that the application use a file-based database. Git inspection
confirmed that the application already uses SQLite, so the work is being
formalized around the SQLite single-file architecture rather than introducing
a different database technology.

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

SQLAlchemy remains the data-access layer and Alembic remains the schema
versioning mechanism.

## Current Application Version

2.0.0 release candidate

Supported database schema:
1-4

## Current Major Features

- Four asset categories
- Generic Asset Fields
- Feed administration
- NVD CPE/CVE intelligence
- CPE applicability foundation
- OSV PURL intelligence
- Vulnerability Candidates
- Admin review workflow
- Approved Vulnerability inventory
- CISA KEV enrichment
- Remediation status
- Sync Jobs and progress
- Five-day NVD discovery window
- SQLite single-file storage

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
