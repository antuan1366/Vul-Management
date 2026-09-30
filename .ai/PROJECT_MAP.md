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

## Project Requirements

requirements.txt

## Project Memory

.ai/

## Important Runtime

Backend development server:

python -m uvicorn app.main:app --reload

The backend is normally started from:

backend/

Because the current Windows environment has PowerShell execution-policy
restrictions, the local virtual-environment Python executable may be used
directly.

Example:

.\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
