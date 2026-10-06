# ARCHITECTURE

## Current Architecture

Browser
    |
    v
Frontend
    |
    | HTTP / JSON
    v
FastAPI
    |
    +-- API Routes
    +-- Services
    +-- Pydantic Schemas
    +-- SQLAlchemy Models
    |
    v
SQLite database file

## Backend

Location:
backend/

Structure:

backend/
└── app/
    ├── api/
    ├── core/
    ├── models/
    ├── schemas/
    ├── services/
    ├── database.py
    └── main.py

### API Layer

Responsible for:
- HTTP endpoints
- Request handling
- Request validation
- Response handling
- HTTP errors

Business logic belongs in services.

### Service Layer

Contains:
- Business logic
- Database operations
- Validation
- Data transformation
- External intelligence integration
- Vulnerability scan scheduling

### Model Layer

SQLAlchemy models represent persistent database entities.

### Database Architecture

Current engine: SQLite.

Default file:
backend/data/vul_management.db

The complete database is stored in one file.

The application uses SQLAlchemy, so API/service code should not depend on SQLite-specific SQL unless there is a deliberate reason.

Alembic is the schema migration mechanism.

The database file is excluded from Git.

### Scan Scheduling

The vulnerability scan schedule is persisted in scan_schedules.

The scheduler stores:
- enabled
- frequency
- daily scan time
- last job ID
- last scan timestamp
- next scan timestamp
- last status
- last error

The FastAPI lifespan starts a lightweight scheduler loop. The loop checks the persisted daily schedule and starts the existing NVD discovery job when due.

The schedule is disabled by default so application startup never unexpectedly launches an external scan.

### Why SQLite

SQLite is a real relational database, not a custom data file.

It provides:
- SQL
- transactions
- indexes
- constraints
- foreign keys
- ACID behavior
- simple backup/restore
- zero separate DB server for local/small deployments

### Future Database Replacement

PostgreSQL remains a possible future deployment database.

The replacement should be handled through the SQLAlchemy/Alembic data layer rather than by rewriting application business logic.

## Asset Architecture

Supported asset types:
- Equipment
- Operating Systems
- Applications
- Libraries

Each asset may have:
- system fields
- custom field definitions
- custom field values
- security identifiers

Security identifiers include CPE and PURL data.

## Vulnerability Architecture

The vulnerability workflow is intentionally separated:

Asset
-> CPE/PURL
-> NVD/OSV
-> Applicability
-> Candidate
-> Pending Review
-> Administrator action
-> Approved / Rejected
-> Asset/Vulnerability mapping
-> CISA KEV
-> Remediation

Candidate data is not the same thing as approved vulnerability inventory.

### Finding State Model

The candidate review state is:
- pending
- approved
- rejected

New discoveries enter pending.

The Vulnerabilities page renders candidate review state directly as the finding status. Approved vulnerability records without a candidate row are also shown as approved.

Admin actions currently available from the findings table:
- Approve
- Reject

## Synchronization Architecture

Long-running discovery operations use Sync Jobs internally.

A Sync Job tracks:
- status
- progress
- processed
- total
- current step
- result
- error
- timestamps

Sync Jobs are an internal execution mechanism. They are no longer exposed as a standalone frontend page.

## Frontend

Location:
frontend/src/

Structure:
- pages/
- services/
- styles/
- layouts/

The frontend is a lightweight HTML/CSS/JavaScript application served by FastAPI.

The Vulnerabilities page is the single UI surface for:
- scan status
- scan scheduling
- manual scan
- CISA KEV update
- finding review

## External Integrations

Dedicated services handle:
- NVD
- CISA KEV
- OSV
- future Nessus integration

Provider-specific logic should not be embedded directly in API routes.

## Security Architecture

Future production requirements:
- Authentication
- Authorization
- RBAC
- Audit logging
- Secret management
- API protection
- Security monitoring

## AI Architecture

AI is not part of the core architecture.

The platform must remain fully functional without AI.


## Latest Vulnerability Scan UX Update

- The Vulnerabilities page now has a single **Scan** button in the upper-right.
- The Scan menu contains:
  - One-time Scan
  - Scheduled Scan
- Scheduled Scan configuration is revealed from the same menu instead of being permanently displayed.
- Vulnerability findings remain on the Vulnerabilities page and are tied to the asset inventory.
- The standalone Scan Results navigation item was removed.
- A scan first evaluates the current asset inventory and refreshes CPE identifiers before NVD discovery.
- If the asset inventory is empty, the scan completes with a `no_assets` state and a clear message that the scan started but no assets are defined.
- If assets exist but none has a resolved CPE, the scan completes with a `no_scannable_assets` state.
- The scan status API exposes the last job result so the Vulnerabilities page can show the scan outcome directly.
