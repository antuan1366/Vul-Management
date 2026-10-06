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

### Model Layer

SQLAlchemy models represent persistent database entities.

### Schema Layer

Pydantic schemas define API request/response contracts.

## Database Architecture

Current engine: SQLite.

Default file:
backend/data/vul_management.db

The complete database is stored in one file.

The application uses SQLAlchemy, so API/service code should not depend on
SQLite-specific SQL unless there is a deliberate reason.

Alembic is the schema migration mechanism.

The database file is excluded from Git.

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

The replacement should be handled through the SQLAlchemy/Alembic data layer
rather than by rewriting application business logic.

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
-> Review
-> Approved Vulnerability
-> Asset/Vulnerability mapping
-> CISA KEV
-> Remediation

Candidate data is not the same thing as approved vulnerability inventory.

## Synchronization Architecture

Long-running discovery operations use Sync Jobs.

A Sync Job tracks:
- status
- progress
- processed
- total
- current step
- result
- error
- timestamps

The frontend polls Sync Job status.

## Frontend

Location:
frontend/src/

Structure:
- pages/
- services/
- styles/
- layouts/

The frontend is a lightweight HTML/CSS/JavaScript application served by
FastAPI.

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
