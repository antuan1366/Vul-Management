# ARCHITECTURE

## Current Architecture

Vul-Management currently uses a simple modular architecture.

Browser
    |
    v
Frontend
    |
    | HTTP/JSON
    v
FastAPI
    |
    +-- API Routes
    |
    +-- Services
    |
    +-- SQLAlchemy Models
    |
    v
SQLite

## Backend

Location:

backend/

Main components:

app/
â”œâ”€â”€ api/
â”œâ”€â”€ core/
â”œâ”€â”€ models/
â”œâ”€â”€ schemas/
â”œâ”€â”€ services/
â”œâ”€â”€ database.py
â””â”€â”€ main.py

### API

API routes are responsible for:
- HTTP endpoints
- Request validation
- Response handling
- HTTP errors

Business logic should stay in services.

### Services

Services contain business logic and database operations.

### Models

SQLAlchemy database models.

### Schemas

Pydantic request and response schemas.

### Database

SQLAlchemy with SQLite during early development.

The database should remain replaceable in the future so PostgreSQL
can be introduced without redesigning the entire application.

## Frontend

Location:

frontend/

The frontend is currently a lightweight HTML/CSS/JavaScript application.

Frontend responsibilities:
- Page rendering
- API calls
- Forms
- Tables
- User interaction

Backend remains the source of truth for business rules and data validation.

## Current API

GET /
GET /api/health

Equipment:

GET /api/equipments
GET /api/equipments/{equipment_id}
POST /api/equipments
PUT /api/equipments/{equipment_id}
DELETE /api/equipments/{equipment_id}

## Future Architecture

The system should eventually support:

Frontend
    |
API
    |
Application Services
    |
Domain/Data Layer
    |
Database

External integrations:

NVD
CISA KEV
Nessus

should communicate through dedicated integration services rather than
being embedded directly into API routes.
