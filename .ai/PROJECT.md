# PROJECT

## Name
Vul-Management

## Repository
GitHub:
antuan1366/Vul-Management

## Current Version
0.1.1

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

The project currently has a functional foundation and an initial
Asset Management implementation.

The Equipment asset type is implemented with:

- Equipment CRUD
- Dynamic Asset Field definitions
- System fields
- Custom fields
- Required / Optional configuration
- Visible / Hidden configuration
- Field type validation
- Asset Field Administration UI
- Equipment management UI

The project is currently focused on building the core platform before
implementing advanced vulnerability intelligence and AI functionality.

## Technology

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
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

The design is intended to be reusable for:

- Equipment
- Operating Systems
- Applications
- Libraries

## Database

SQLite is currently used for development.

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

0.1.1

The 0.1.x series represents the early development phase of the platform.

Minor version increases should be used for meaningful new functionality.

Patch version increases should be used for fixes and smaller improvements.

Major version 1.0.0 should only be considered when the core platform is
stable and sufficiently production-ready.
