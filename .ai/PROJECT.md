# PROJECT

## Name
Vul-Management

## Repository
GitHub:
antuan1366/Vul-Management

## Current Version
1.0.0

## Description
Vul-Management is a modular web-based vulnerability management platform.

The platform is designed to provide centralized management for:

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

## Current Development Status

Version 1.0.0 establishes the first complete Asset Management foundation.

Implemented asset types:

- Equipment
- Operating Systems
- Applications
- Libraries

The current release includes:

- CRUD APIs for all four asset categories
- Generic Asset Field definitions
- Asset-specific system fields
- Custom fields and custom values
- Required / Optional configuration
- Visible / Hidden configuration
- Asset Field Administration UI
- Dynamic Add/Edit forms for managed assets
- Equipment table with dynamic field labels
- FastAPI-hosted frontend under /src
- Root redirect to the dashboard
- API metadata endpoint at /api/info
- Alembic database versioning
- Database schema compatibility validation

The project is currently focused on building the core platform before
implementing advanced vulnerability intelligence and AI functionality.

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

## Architecture Principles

The application should remain modular and easy to troubleshoot.

Backend responsibilities are separated into:

- API routes
- Models
- Schemas
- Services
- Core / configuration

Frontend responsibilities are separated into:

- Pages
- Services
- Styles
- API communication

The frontend is served by FastAPI in the current integrated runtime.

## Asset Field Architecture

The project uses a generic Asset Field system.

Each asset type can have:

- Predefined system fields
- Custom fields
- Required / Optional configuration
- Visible / Hidden configuration
- Editable / Non-editable configuration
- Field type validation
- Select / Multiselect options

System-critical fields are protected from deletion where required.

Custom fields are stored through the generic asset field/value system.

The design is reusable across:

- Equipment
- Operating Systems
- Applications
- Libraries

## Database

SQLite is currently used for development.

Alembic is the schema-versioning mechanism. The current baseline is
schema revision 0001, and application version 1.0.0 supports DB schema 1.

The database architecture should remain replaceable so that PostgreSQL
or another production database can be introduced later without requiring
a complete application redesign.

## Vulnerability Intelligence

Planned sources include:

- NVD / CVE
- CISA KEV
- Manual vulnerability entry
- Nessus findings

## AI

AI functionality is currently OUT OF SCOPE.

Mem0, local LLMs and AI-assisted vulnerability analysis may be added later.

Core application functionality must never depend on AI.

## Development Philosophy

Development is incremental.

Each major component should be:

1. Designed
2. Implemented
3. Tested locally
4. Reviewed through API/UI
5. Approved
6. Documented
7. Committed to Git

GitHub releases should represent stable development checkpoints.

## Versioning

Current version:

1.0.0

Version 1.0.0 is the first consolidated Asset Management release and
includes the Asset Types implementation, database versioning foundation,
and FastAPI/frontend integration.

Future versioning should use semantic-versioning principles:

- Patch versions for fixes and small corrections
- Minor versions for backward-compatible feature additions
- Major versions for breaking changes

The next major development area after this release is Vulnerability Management.
