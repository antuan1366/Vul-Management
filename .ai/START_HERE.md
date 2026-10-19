# START HERE

## Project
Vul-Management — version 3.2.0

- Repository: `antuan1366/Vul-Management`
- Development branch: `develop`
- Documentation update branch: `docs/v3.2.0-tested`
- Stack: FastAPI, SQLAlchemy, Alembic, SQLite, plain HTML/CSS/JavaScript.

## Read order
1. `PROJECT.md`
2. `STATE.md`
3. `SESSION.md`
4. `STRATEGY.md`
5. `ARCHITECTURE.md`
6. `PROJECT_MAP.md`
7. `UI_STYLE_GUIDE.md`
8. `DECISIONS.md`
9. `TODO.md`
10. `RULES.md`
11. `COMPATIBILITY.md`
12. `V3.2.0_RELEASE.md`

Inspect actual source files relevant to the task. If documentation and code disagree, report the mismatch and verify behavior.

## Current feature areas
- Asset Management: Equipment, Operating Systems, Applications, Libraries.
- Administrator-managed asset fields.
- Threat Intelligence and scan results.
- Telegram feed administration and CVE discovery/review.
- Nessus manual scan, findings review, and host mapping.
- Administration and Logs & Events.
- Jira integration must be verified end-to-end before being presented as production-ready.

## User-reported local smoke test
The user reports the app starts and six page groups open successfully. This is not proof that all business workflows or integrations have been tested. See `V3.2.0_RELEASE.md`.

## Database safety
- Default SQLite path: `backend/data/vul_management.db`.
- Never delete, reset, recreate, or overwrite `backend/data/` to solve a code issue without explicit approval and a verified backup.
- Never commit databases, credentials, tokens, Telegram session files, or private keys.
- Use Alembic for schema changes and verify the database path before migrations.

## Git workflow
- Work on `develop` or a focused feature branch.
- Inspect `git status` before risky operations.
- Do not force-push, reset local history, use `git clean`, or merge into `main` without explicit approval for that action.
- Keep releases retrievable using immutable version tags/releases after verification and release approval.

## Current priority
Finish end-to-end workflow testing, then create a clean customer deployment package and test it on a separate machine. Keep claims about verification precise.
