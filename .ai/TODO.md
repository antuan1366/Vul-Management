# TODO

## Current Release

Version: 1.1.0

## Release Checklist

### Code and Documentation
- [x] Equipment CRUD implementation
- [x] Generic Asset Field system
- [x] Asset Field Administration UI
- [x] Equipment Add/Edit floating modal
- [x] Asset Field Add/Edit floating modal
- [x] Required / Optional field configuration
- [x] Visible / Hidden field configuration
- [x] Automatic custom field key generation
- [x] Operating Systems asset type
- [x] Applications asset type
- [x] Libraries asset type
- [x] Dynamic managed-asset frontend
- [x] Alembic database versioning
- [x] Database compatibility validation
- [x] FastAPI-hosted frontend
- [x] Dynamic Equipment table field labels
- [x] Version updated to 1.0.0
- [x] .ai documentation updated

### Local Verification
- [x] Verify local application starts
- [x] Verify database schema version
- [x] Verify Equipment CRUD
- [x] Verify Asset Field CRUD
- [x] Verify Equipment Add/Edit modal
- [x] Verify Asset Field Add/Edit modal
- [x] Verify required/visible behavior
- [x] Verify custom field validation
- [x] Verify Delete actions
- [x] Verify frontend behavior
- [x] Verify Equipment field-label refresh

### Release
- [x] Final release candidate prepared on feature branch
- [ ] Create Pull Request: feature/frontend-fastapi-integration -> main
- [ ] User review Pull Request
- [ ] User merge Pull Request
- [ ] Synchronize local main
- [ ] Create Git tag v1.0.0

## Asset Management

### Equipment
- [x] Equipment model
- [x] Equipment CRUD
- [x] Equipment frontend
- [x] Generic Asset Field system
- [x] Custom Equipment fields
- [x] Required / Optional fields
- [x] Visible / Hidden fields
- [x] Field type validation
- [x] Asset Field Administration

### Operating Systems
- [x] Operating System model
- [x] Operating System schema
- [x] Operating System service
- [x] Operating System API
- [x] Operating System frontend
- [x] Operating System custom fields
- [x] Equipment relationship

### Applications
- [x] Application model
- [x] Application schema
- [x] Application service
- [x] Application API
- [x] Application frontend
- [x] Application custom fields
- [x] Asset relationships

### Libraries
- [x] Library model
- [x] Library schema
- [x] Library service
- [x] Library API
- [x] Library frontend
- [x] Library custom fields
- [x] Application relationships

## Vulnerability Management
- [x] Vulnerability model
- [ ] Vulnerability schema
- [ ] Vulnerability CRUD
- [ ] CVE
- [ ] Severity
- [ ] Product
- [ ] Description
- [ ] Affected versions
- [ ] Remediation
- [ ] Mitigation
- [ ] Workaround
- [ ] Status
- [ ] Dates
- [ ] References
- [ ] Vulnerability frontend
- [ ] Remediation tracking
- [ ] Asset/Vulnerability relationship

## Vulnerability Intelligence
- [x] NVD CPE feed configuration
- [x] NVD CVE correlation foundation
- [x] CISA KEV synchronization
- [x] Feed Administration UI
- [x] Security identifier storage (CPE/PURL)
- [x] Asset/Vulnerability mapping model
- [ ] Full NVD incremental synchronization
- [ ] OSV synchronization by PURL
- [ ] Complete applicability/version-range engine
- [ ] Manual applicability override

## Scanning
- [ ] Nessus import
- [ ] Finding normalization
- [ ] Asset matching
- [ ] Vulnerability matching
- [ ] Scan result management

## Risk Management
- [ ] Risk calculation
- [ ] Severity weighting
- [ ] Asset criticality weighting
- [ ] CISA KEV weighting
- [ ] Exposure weighting
- [ ] Environment weighting
- [ ] Explainable risk calculation

## Reporting
- [ ] Dashboard
- [ ] Asset statistics
- [ ] Vulnerability statistics
- [ ] Critical/High findings
- [ ] Remediation statistics
- [ ] Trend reporting
- [ ] Vulnerability reports
- [ ] Remediation reports
- [ ] Export functionality

## Security
- [ ] Authentication
- [ ] Authorization
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Secure configuration
- [ ] API protection
- [ ] Input security review

## Future
- [ ] AI assistant
- [ ] Local/private AI integration
- [ ] Natural language vulnerability analysis
- [ ] AI-assisted reporting
- [ ] AI-assisted remediation guidance

AI must remain optional and must not be required by the core platform.
