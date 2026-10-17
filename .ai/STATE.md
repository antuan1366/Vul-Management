# STATE

## Snapshot
- Project: Vul-Management
- Active branch: `develop`
- Target version: `3.1.0`
- Backend and sidebar version declarations: `3.1.0`
- Target Alembic revision: `0008`
- Source changes are not a claim of runtime verification.

## Existing platform
- FastAPI, SQLAlchemy, Alembic, SQLite, and plain HTML/CSS/JavaScript.
- Existing Telegram scan/review workflow and shared Vulnerability Register.
- Runtime database: `backend/data/vul_management.db`; preserve it and never commit it.

## Nessus 3.1.0
- Upload `.nessus` / `.xml` files up to 25 MB and explicitly analyse after upload.
- Uses defusedxml; report metadata and plugin findings are stored in dedicated tables.
- Nessus Scan Result has New, Under Review, Accept and Reject tabs and table settings.
- Accepted findings with valid CVEs create/link records in the same `threat_intelligence` table used by Telegram.
- Findings without CVEs remain in Nessus Scan Result and cannot enter the CVE register.
- Administration → Nessus Host Mapping maps hostname/FQDN/IP/MAC/UUID values to a canonical hostname for future analyses.
- Original host identifiers and plugin evidence remain available.

## Compatibility and verification
- Migration 0008 is additive and creates Nessus import, finding and host mapping tables.
- Install `python-multipart` and `defusedxml` before startup.
- Runtime migration/API/browser tests and validation against a real Nessus export remain outstanding.
- Do not merge to `main` without explicit approval.
