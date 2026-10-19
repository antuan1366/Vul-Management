# SESSION

## Current state
- Current version: 3.2.0.
- Main and develop were synchronized before local testing; this documentation change is prepared separately on `docs/v3.2.0-tested`.
- The user reports successful local startup and successful page-level smoke checks for Asset Management, Nessus Manual Scan, Nessus Scan Results, Threat Intelligence, Administration, and Logs & Events.

## Nessus workflow in source
- Manual Scan page supports Nessus file upload and a separate analysis action.
- The backend declares parsing dependencies including `defusedxml` and `python-multipart`.
- Findings review and host mapping are present in the current source.
- Do not treat page visibility as proof that file upload, XML parsing, finding acceptance, deduplication, or mapping has passed end-to-end testing.

## Next verification
1. Check `/api/info` reports version 3.2.0 and the expected schema version.
2. Check Alembic current/history and migration behavior against a backed-up test database before any customer migration.
3. Upload and analyse a synthetic Nessus XML fixture; verify expected host and finding counts.
4. Test New, Under Review, Accept, and Reject actions.
5. Confirm accepted CVE findings appear once in the shared vulnerability register and findings without CVEs cannot be promoted.
6. Test hostname/FQDN/IP/MAC/UUID host mapping.
7. Exercise Telegram scan, review, NVD enrichment, and promotion with controlled test data.
8. Verify Jira integration with a test project before enabling it for a customer.
9. Prepare and test a clean deployment package on a separate machine.

## Safety
- Preserve the local runtime database.
- Do not change `.ai/` on the user's working copy until the documentation PR is reviewed/merged and pulled.
- Do not claim unperformed API, migration, integration, or clean-machine tests.
