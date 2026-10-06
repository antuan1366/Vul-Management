# STRATEGY

## Development Strategy

Build Vul-Management incrementally.

Every major component follows:

1. Design
2. Implementation
3. Local testing
4. API testing
5. UI review
6. Documentation update
7. Git commit
8. User approval before merge

## Current Release Candidate

2.0.0

## Phase 1 - Foundation

Status: COMPLETED

Implemented:
- FastAPI
- SQLAlchemy
- Alembic
- SQLite
- Modular backend/frontend structure
- Health endpoint
- Database compatibility validation

## Phase 2 - Asset Management

Status: COMPLETED

Implemented:
- Equipment
- Operating Systems
- Applications
- Libraries
- Generic Asset Fields
- Dynamic managed-asset forms

## Phase 3 - Vulnerability Intelligence

Status: IMPLEMENTED FOUNDATION

Implemented:
- Feed administration
- NVD CPE
- NVD CVE discovery
- CPE applicability foundation
- OSV PURL discovery
- Security identifiers
- Five-day default NVD discovery window

## Phase 4 - Candidate and Review Workflow

Status: IMPLEMENTED FOUNDATION

Implemented:
- Vulnerability Candidate model
- Pending Review UI
- Approve
- Reject
- Approved Vulnerability inventory
- Asset/Vulnerability mapping
- CISA KEV enrichment for approved records
- Sync Status

## Phase 5 - Risk Management

Status: NEXT MAJOR FUNCTIONAL AREA

Implement:
- Risk calculation
- Asset criticality weighting
- CVSS weighting
- KEV weighting
- Exposure weighting
- Environment weighting
- Explainable risk score

## Phase 6 - Nessus Integration

Implement:
- Nessus file import
- Finding normalization
- Asset matching
- Vulnerability matching
- Finding status
- Remediation tracking

## Phase 7 - Remediation

Implement:
- Full remediation UI
- SLA/dates
- Ownership
- Exceptions
- Evidence
- Closure workflow

## Phase 8 - Dashboard and Reporting

Implement:
- Asset statistics
- Vulnerability statistics
- Critical/High findings
- Remediation status
- Trends
- Reports
- Export

## Phase 9 - Security

Implement:
- Authentication
- Authorization
- RBAC
- Audit logging
- Secure configuration
- API protection
- Security review

## Phase 10 - AI

AI remains optional and postponed until the core platform is stable.

Possible future capabilities:
- Vulnerability analysis
- Natural-language queries
- Remediation assistance
- Asset intelligence
- Reporting assistance

The platform must remain fully functional without AI.
