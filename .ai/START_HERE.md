# START HERE

## Project
Vul-Management

## Purpose
Vul-Management is a vulnerability management platform for assets,
vulnerabilities, vulnerability intelligence, remediation tracking and
reporting.

## Current Release Candidate
2.0.0

## Current Branch
feature/v2-sqlite-foundation

## Current Development State

The project has progressed beyond the original Asset Management foundation.

Implemented:
- Equipment
- Operating Systems
- Applications
- Libraries
- Generic Asset Fields
- Feed administration
- NVD CPE resolution and CVE discovery
- OSV PURL discovery
- Applicability foundation
- Vulnerability Candidate workflow
- Admin approval/rejection
- Approved Vulnerability inventory
- CISA KEV enrichment
- Remediation status
- Sync Jobs and progress
- SQLite single-file database
- Alembic schema versioning

## Database

Database engine:
SQLite

Default file:
backend/data/vul_management.db

The database file is local runtime state and is ignored by Git.

Do not replace the SQLite file with a JSON/YAML/custom storage format.
SQLite already provides transactions, indexes, constraints and SQL while
keeping the database in one portable file.

## Read Order

1. PROJECT.md
2. STRATEGY.md
3. ARCHITECTURE.md
4. PROJECT_MAP.md
5. STATE.md
6. SESSION.md
7. DECISIONS.md
8. TODO.md
9. RULES.md
10. COMPATIBILITY.md

## Immediate Goal

Verify the 2.0.0 release candidate locally before any merge to main.

The user performs the final merge.
