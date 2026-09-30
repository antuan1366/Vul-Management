# PROJECT

## Name
Vul-Management

## Repository
GitHub repository:
antuan1366/Vul-Management

## Description
Vul-Management is a web-based vulnerability management platform.

The application is intended to provide a centralized system for:

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
2. Operating System
3. Applications
4. Libraries

## Vulnerability Intelligence

Planned intelligence sources:

- NVD / CVE
- CISA KEV
- Manual vulnerability entry
- Nessus findings

## Future AI

An AI assistant may be added later using local/private AI or other
integrations.

AI is currently OUT OF SCOPE.

Core functionality has priority over AI functionality.

## Current Version

0.1.0

## Technology

Backend:
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite

Frontend:
- HTML
- CSS
- JavaScript

## Development Philosophy

The project should remain modular and easy to troubleshoot.

Backend functionality should be separated into:
- API routes
- Models
- Schemas
- Services
- Core/configuration

Frontend functionality should also be split into separate pages and services.
