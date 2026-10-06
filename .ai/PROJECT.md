# PROJECT

## Name
Vul-Management

## Repository
GitHub:
antuan1366/Vul-Management

## Current Release Candidate
2.0.0

## Description
Vul-Management is a modular web-based vulnerability management platform for:

- Asset Management
- Vulnerability Management
- Vulnerability Intelligence
- Asset-to-Vulnerability Mapping
- Risk Prioritization
- Remediation Tracking
- Nessus Integration
- Reporting and Dashboarding

## Main Asset Categories

1. Equipment
2. Operating Systems
3. Applications
4. Libraries

## Current Development State

The 2.0.0 release candidate consolidates the vulnerability-intelligence
foundation and introduces the Candidate -> Review -> Approved workflow.

Implemented:

- CRUD for all four asset categories
- Generic Asset Field system
- Feed administration
- Security identifiers
- NVD CPE resolution
- NVD CVE discovery
- CPE applicability/version-range foundation
- OSV PURL discovery
- Candidate vulnerability workflow
- Admin approve/reject workflow
- Asset/Vulnerability mapping
- CISA KEV enrichment for approved vulnerabilities
- Remediation status API
- Synchronization jobs and progress tracking
- Five-day default NVD discovery window
- FastAPI-hosted frontend
- Alembic database versioning
- SQLite single-file database

## Technology

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- SQLite

### Frontend
- HTML
- CSS
- JavaScript

## Database Architecture

SQLite is the current application database.

Default database:

backend/data/vul_management.db

The database is one physical file and is intentionally excluded from Git
through .gitignore.

SQLAlchemy remains the application data-access layer and Alembic remains the
schema migration mechanism.

The architecture keeps the database layer replaceable so PostgreSQL can be
introduced later if deployment scale requires it.

### Backup Principle

Because the database is a file, the SQLite database can be backed up by
copying the database file while the application is stopped.

Production backup/restore procedures must be defined before production use.

## Vulnerability Workflow

Asset
-> CPE / PURL
-> NVD / OSV discovery
-> Vulnerability Candidate
-> Administrator Review
-> Approved Vulnerability
-> Asset/Vulnerability mapping
-> CISA KEV enrichment
-> Risk
-> Remediation

A discovered finding must not automatically become an approved vulnerability.

## AI

AI functionality is OUT OF SCOPE for the 2.0.0 core release.

Mem0, local LLMs and AI-assisted analysis remain optional future work.

## Versioning

Semantic versioning is used:

- Patch: fixes
- Minor: backward-compatible features
- Major: breaking architecture or workflow changes

Version 2.0.0 is the next major release candidate. It must not be treated
as the main-branch release until the user completes local verification and
explicitly approves the merge.
