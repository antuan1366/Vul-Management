# STRATEGY

## Development Strategy

Build Vul-Management incrementally.

Do not implement the entire platform at once.

Every major component should follow:

1. Design
2. Implementation
3. Local testing
4. API testing
5. UI review
6. Documentation update
7. Git commit

Do not push unfinished functionality as a stable development checkpoint.

## Current Version

0.1.1

The current version represents the first structured development
checkpoint after establishing the initial Asset Management foundation.

## Phase 1 - Foundation

Status: COMPLETED

Implemented:

- Project structure
- FastAPI
- Configuration
- Database layer
- SQLAlchemy
- SQLite
- Health endpoint
- Modular backend structure
- Modular frontend structure

## Phase 2 - Asset Management

Status: RELEASE CANDIDATE

### Equipment

Status: IMPLEMENTED

Implemented:

- Equipment model
- Equipment CRUD
- Equipment frontend
- Generic Asset Field engine
- System fields
- Custom fields
- Required / Optional
- Visible / Hidden
- Field validation
- Asset Field Administration
- Floating modal UX for Equipment Add/Edit
- Floating modal UX for Asset Field Add/Edit

### Operating Systems

Status: PLANNED

Order:

1. Model
2. Schema
3. Service
4. API
5. Frontend
6. Custom fields
7. Equipment relationship

### Applications

Status: PLANNED

Order:

1. Model
2. Schema
3. Service
4. API
5. Frontend
6. Custom fields
7. Asset relationships

### Libraries

Status: PLANNED

Order:

1. Model
2. Schema
3. Service
4. API
5. Frontend
6. Custom fields
7. Application relationships

## Phase 3 - Vulnerability Management

Implement:

- Vulnerability database
- CVE
- Severity
- Product
- Description
- Affected versions
- Remediation
- Mitigation
- Workaround
- Status
- Dates
- References

The vulnerability model should be independent from external intelligence
providers.

Manual vulnerability records must remain possible.

## Phase 4 - Vulnerability Intelligence

Integrate:

- NVD
- CISA KEV

External intelligence should be handled by dedicated integration
services.

Imported information must not blindly overwrite manually maintained
information.

The system should preserve source information and synchronization
metadata.

## Phase 5 - Asset/Vulnerability Mapping

Create relationships between:

- Equipment
- Operating Systems
- Applications
- Libraries
- Vulnerabilities

The mapping must support:

- Applicability
- Manual override
- Evidence
- Mapping status

## Phase 6 - Risk Management

Implement explainable risk prioritization using factors such as:

- Severity
- Exploitability
- CISA KEV status
- Asset criticality
- Environment
- Exposure

Risk calculations should be explicit and auditable.

## Phase 7 - Nessus Integration

Support:

- Nessus file import
- Finding normalization
- Asset matching
- Vulnerability matching
- Finding status
- Remediation tracking

Nessus should be treated as an external source rather than the core
vulnerability data model.

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
- Role-based access control
- Audit logging
- Secure configuration
- API protection
- Security review

Security work becomes increasingly important as the application moves
toward production use.

## Phase 10 - AI

AI should only be implemented after the core platform is stable.

Possible capabilities:

- Vulnerability analysis
- Natural language queries
- Remediation assistance
- Asset intelligence
- Reporting assistance

AI must remain optional.

The platform must remain fully functional without AI.
