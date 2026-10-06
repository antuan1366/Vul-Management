# PROJECT MAP

## Root

E:\Vul-Management

## Backend

backend/

### Configuration
backend/app/core/

### API
backend/app/api/

### Models
backend/app/models/

### Schemas
backend/app/schemas/

### Services
backend/app/services/

### Database
backend/app/database.py

### Migrations
backend/alembic/versions/

### Application Entry Point
backend/app/main.py

## Frontend

frontend/

### Pages
frontend/src/pages/

### Services
frontend/src/services/

### Styles
frontend/src/styles/

### Layouts
frontend/src/layouts/

## Runtime Database

backend/data/vul_management.db

This file is ignored by Git.

## Project Memory

.ai/

## Important Runtime

Start backend from:

backend/

Command:

python -m uvicorn app.main:app --reload

If PowerShell execution policy blocks activation, use the virtual environment
Python executable directly.

## Main Verification URLs

Dashboard:
http://127.0.0.1:8000/

API info:
http://127.0.0.1:8000/api/info

Swagger:
http://127.0.0.1:8000/docs
