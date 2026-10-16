# TODO

This list separates verification and known gaps from intended future work. Update checkboxes only after testing the actual implementation.

## Immediate UI and workflow verification
- [ ] Change the Threat Intelligence child label from “Vulnerability Register” to the intended “Vulnerabilities” and verify active navigation (if still desired).
- [ ] Verify every page loads through the FastAPI-hosted frontend.
- [ ] Verify sidebar collapse/expand and selected parent/child state on every route.
- [ ] Verify Table Setting on every integrated table: dialog opens/closes, columns toggle, widths resize, preferences persist, pagination works.
- [ ] Verify responsive layout for page headers, forms, dialogs and wide tables.

## Telegram to CVE workflow
- [ ] Verify Telegram feeds can be created, edited, enabled/disabled and deleted as intended.
- [ ] Verify Telegram account/session setup and verification behavior with a test account.
- [ ] Verify scanning of configured public channels.
- [ ] Verify scan mode/schedule and from-date behavior against the actual implementation.
- [ ] Verify CVE extraction and deduplication.
- [ ] Verify scan-result DATE represents system intake time if this remains the approved requirement.
- [ ] Verify original Telegram message/channel context is retained.
- [ ] Verify table summaries are concise and full message content is accessible on hover or in details.
- [ ] Verify administrator accept/reject actions.
- [ ] Verify NVD enrichment for severity, affected product/version and remediation/mitigation when NVD provides data.
- [ ] Verify accepted/approved records are promoted to the intended Vulnerabilities/Threat Intelligence inventory.
- [ ] Verify failures, rate limits, duplicate messages and unavailable NVD data are handled clearly.
- [ ] Jira issue creation integration (not complete until implemented and tested).

## Asset management
- [ ] Verify CRUD for Equipment.
- [ ] Verify CRUD for Operating Systems.
- [ ] Verify CRUD for Applications.
- [ ] Verify CRUD for Libraries.
- [ ] Verify asset-specific custom fields and required/visible behavior.
- [ ] Verify CPE/PURL identification and vulnerability mapping where implemented.

## Vulnerability management
- [ ] Verify vulnerability feed administration and connectivity testing.
- [ ] Verify vulnerability scan status, errors and progress.
- [ ] Verify candidate review states and approved inventory.
- [ ] Verify remediation workflow and statuses.
- [ ] Verify CVE data/source links and table usability.

## Future work
- [ ] Dashboard metrics and useful reporting.
- [ ] Risk prioritization with explainable factors.
- [ ] Nessus import and finding normalization.
- [ ] Remediation ownership, due dates/SLA and exception workflow.
- [ ] Authentication, authorization/RBAC, audit logging and production security review.
- [ ] Optional AI assistance only after explicit approval and stable core workflows.

## Release gate
- [ ] Run backend startup and migration checks.
- [ ] Run relevant automated tests.
- [ ] Perform UI/API smoke tests for affected workflows.
- [ ] Review Git diff and ensure no runtime DB/secrets are included.
- [ ] Update `.ai/STATE.md`, `.ai/SESSION.md`, `.ai/COMPATIBILITY.md` and this TODO as appropriate.
- [ ] User approves any promotion/merge to `main`.
