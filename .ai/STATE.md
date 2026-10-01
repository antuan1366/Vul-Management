# STATE

## Version
1.2.0

## State
VULNERABILITY INTELLIGENCE + APPLICABILITY FOUNDATION

The current feature branch extends the 1.1.0 intelligence foundation.

## Implemented

- Asset Management: Equipment, Operating Systems, Applications, Libraries
- Generic Asset Fields
- Feed Administration
- NVD CPE resolution
- NVD CVE correlation
- CISA KEV synchronization
- Security Identifier storage
- NVD applicability/version evaluation foundation
- Incremental NVD synchronization
- OSV PURL synchronization
- Asset identifier refresh
- Asset/Vulnerability mapping
- Remediation status API
- Asset-level vulnerability synchronization controls
- NVD synchronization control in Vulnerabilities UI

## Intelligence Pipeline

Asset
-> Vendor/Product/Version
-> CPE or PURL
-> NVD / OSV
-> Applicability evaluation
-> Asset/Vulnerability mapping
-> CISA KEV enrichment
-> Remediation tracking

A CPE match alone is not treated as confirmed vulnerability when an
applicability rule can be evaluated.

## Database

Alembic revisions:
- 0001 baseline
- 0002 vulnerability intelligence
- 0003 feed synchronization metadata

Application version: 1.2.0
Supported schema: 1-3

## Remaining Major Work

1. Improve CPE/PURL automatic resolution and confidence scoring
2. Manual applicability override UI
3. Full vulnerability/remediation UI
4. Risk calculation and prioritization
5. Nessus import and finding normalization
6. Reporting/export
7. Authentication/authorization/audit logging
8. AI/Mem0 remains optional and postponed

## Git

Current feature branch:
feature/applicability-osv-remediation

The branch is based on:
feature/vulnerability-intelligence-feeds

Do not merge automatically. User performs local verification and merge.
