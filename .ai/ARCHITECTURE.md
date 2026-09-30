# ARCHITECTURE

## Current Architecture

Vul-Management currently uses a modular web application architecture.

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
    |
    +-- Services
    |
    +-- Pydantic Schemas
    |
    +-- SQLAlchemy Models
    |
    v
SQLite

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

API routes are responsible for:

- HTTP endpoints
- Request handling
- Request validation
- Response handling
- HTTP errors

Business logic should remain inside services.

### Service Layer

Services contain:

- Business logic
- Database operations
- Validation
- Data transformation

### Model Layer

SQLAlchemy models represent persistent database entities.

### Schema Layer

Pydantic schemas define:

- API requests
- API responses
- Validation contracts

## Database

SQLite is currently used during development.

The database should remain replaceable.

PostgreSQL or another production database should be possible later
without redesigning the complete application architecture.

## Asset Architecture

Equipment is currently the first implemented asset type.

Equipment contains core system fields directly in its database model.

Generic Asset Field definitions and values are stored separately.

Conceptually:

Asset
 |
 +-- System Fields
 |
 +-- Custom Field Definitions
 |
 +-- Custom Field Values

The generic field engine is designed to be reused by:

- Equipment
- Operating Systems
- Applications
- Libraries

## Asset Field System

The Asset Field system contains:

### AssetFieldDefinition

Defines:

- asset_type
- field_key
- label
- field_type
- required
- visible
- system_field
- editable
- deletable
- options
- description

### AssetFieldValue

Stores:

- asset_type
- asset_id
- field_id
- value

This separation allows asset-specific custom fields without creating
a new database column for every custom requirement.

## Current API

### Core

GET /

GET /api/health

### Equipment

GET /api/equipments

GET /api/equipments/{equipment_id}

POST /api/equipments

PUT /api/equipments/{equipment_id}

DELETE /api/equipments/{equipment_id}

### Asset Fields

GET /api/asset-fields

POST /api/asset-fields

PUT /api/asset-fields/{field_id}

DELETE /api/asset-fields/{field_id}

## Frontend

Location:

frontend/

The frontend is a lightweight HTML/CSS/JavaScript application.

Responsibilities:

- Page rendering
- API communication
- Forms
- Tables
- Navigation
- User interaction

Frontend pages are separated from reusable services.

Current conceptual structure:

frontend/
└── src/
    ├── pages/
    ├── services/
    └── styles/

## Navigation

The frontend uses a shared sidebar/navigation structure.

Current conceptual sections:

- Dashboard
- Assets
  - Equipment
  - Operating Systems
  - Applications
  - Libraries
- Vulnerabilities
  - Vulnerabilities
  - Remediation
  - Scan Results
- Intelligence
  - NVD
  - CISA KEV
- Reporting
  - Dashboard
  - Reports
- Administration
  - Asset Fields

Some sections are currently placeholders for future functionality.

## Backend as Source of Truth

The backend remains responsible for:

- Validation
- Required field enforcement
- Field type validation
- Business rules
- Database consistency

Frontend validation exists for usability but must not replace backend
validation.

## External Integrations

Future integrations should use dedicated services.

Planned integrations:

- NVD
- CISA KEV
- Nessus

These integrations should not place provider-specific logic directly
inside API route handlers.

## Future Architecture

The long-term architecture is:

Frontend
    |
API
    |
Application Services
    |
Domain / Data Layer
    |
Database

External integrations:

NVD
CISA KEV
Nessus

should communicate through dedicated integration services.

## Future Security Architecture

The application will eventually require:

- Authentication
- Authorization
- Role-based access control
- Audit logging
- Secure API configuration
- Secret management
- Input validation
- Security monitoring

## AI Architecture

AI is intentionally not part of the current core architecture.

If introduced later, AI should communicate with the platform through
well-defined services/interfaces.

AI must not become tightly coupled to:

- Database models
- Core business rules
- Asset CRUD
- Vulnerability CRUD
- Authentication

The core application must remain fully functional without AI.
