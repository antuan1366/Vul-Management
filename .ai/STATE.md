# STATE

## Version
2.0.0 release candidate

## State
VULNERABILITY INTELLIGENCE + APPROVAL WORKFLOW + SQLITE FOUNDATION

The current candidate is based on the approved-findings/sync-status feature
line and is being prepared as the next major release.

## Implemented

- Asset Management: Equipment, Operating Systems, Applications, Libraries
- Generic Asset Fields
- Feed Administration
- NVD CPE resolution
- NVD CVE discovery
- CPE applicability/version evaluation foundation
- OSV PURL synchronization
- Security Identifier storage
- Vulnerability Candidate storage
- Candidate approve/reject workflow
- Approved Vulnerability inventory
- Asset/Vulnerability mapping
- CISA KEV enrichment
- Remediation status API
- Asset identifier extraction
- Sync Jobs with progress/status
- Five-day default NVD discovery window
- SQLite single-file database

## Intelligence Pipeline

Asset
-> Vendor/Product/Version
-> CPE or PURL
-> NVD / OSV
-> Applicability evaluation
-> Vulnerability Candidate
-> Admin Review
-> Approved Vulnerability
-> Asset/Vulnerability mapping
-> CISA KEV
-> Remediation

A CPE match alone is not automatically treated as a confirmed approved
vulnerability.

## Database

Engine:
- SQLite

Database file:
- backend/data/vul_management.db

Alembic revisions:
- 0001 baseline
- 0002 vulnerability intelligence
- 0003 feed synchronization metadata
- 0004 candidate workflow and sync jobs

Supported schema:
- 1-4

The local database file is ignored by Git.

## Git

Current branch:
feature/v2-sqlite-foundation

Base:
feature/approved-findings-sync-status

This branch is a release-candidate preparation branch. It must not be merged
automatically.

The user performs local verification and the final merge.

## Immediate Verification

1. Start backend successfully.
2. Confirm database bootstrap and schema 4.
3. Confirm Approved Vulnerabilities is empty after the development reset.
4. Create test assets.
5. Extract CPE/PURL identifiers.
6. Run NVD/OSV discovery.
7. Confirm discoveries appear as Pending Review.
8. Approve one candidate and reject another.
9. Confirm only approved findings enter the approved inventory.
10. Verify CISA KEV enriches approved findings.
11. Verify Sync Status progress.
12. Verify the SQLite file is created under backend/data.
