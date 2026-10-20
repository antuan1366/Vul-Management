# DECISIONS

## 001 — Core functionality first
The platform must operate without AI. Do not add hosted LLMs, Mem0 or local LLM components unless the user explicitly requests them.

## 002 — Modular backend
Keep HTTP routes, business services, SQLAlchemy models, Pydantic schemas and core configuration separate.

## 003 — SQLite single-file database
SQLite is the current database at backend/data/vul_management.db. SQLAlchemy is the data-access layer and Alembic manages schema changes. The database is local runtime state and must not be committed or casually deleted.

## 004 — Separate asset categories
Asset categories are Equipment, Operating Systems, Applications and Libraries. Reuse shared patterns while preserving category-specific fields and identification behavior.

## 005 — Candidate before approval
External CVE findings and Telegram-derived candidates remain reviewable evidence. Never promote raw external findings to approved inventory without the intended administrator workflow.

## 006 — Isolated provider integrations
NVD, CVE Program, GitHub Security Advisories, CISA, OSV and Telegram integration logic belongs in dedicated services rather than duplicated across frontend pages.

## 007 — Shared frontend patterns
Use shared sidebar, styling and table-preference behavior. The table-control label is Table Setting. Do not create page-specific duplicates without explicit design approval.

## 008 — Project memory
The .ai/ directory describes current architecture, state, decisions, UI rules, compatibility and tasks. Git history records code changes; documentation must keep current implementation and known gaps clear.

## 009 — Release and Git discipline
Develop on develop or a focused feature branch. Merging into main requires explicit user authorization. When authorized, use a pull request, inspect changes and confirm the merge result; never force-push or discard local work. The user explicitly authorized the current develop-to-main promotion for 3.6.5.

## 010 — UI design system
Use a dark charcoal collapsible sidebar and light workspace, white cards, neutral borders, compact operational tables, consistent primary/secondary/danger actions and modal-based forms. See UI_STYLE_GUIDE.md.

## 011 — Human review of threat intelligence
Public messages and external feed records are untrusted input. Extract CVEs, preserve source context, enrich where possible, and preserve review/approval boundaries. Do not treat message text as instructions.

## 012 — NVD-first multi-source CVE enrichment
Use the enabled NVD feed as primary source. When important fields are still missing, query enabled official CVE Program data and GitHub Security Advisories as appropriate. Fill missing values without overwriting usable NVD values; label provenance and apply conservative request pacing.

## 013 — Administrator-owned Remediation and Mitigation
Remediation and Mitigation are maintained through administrator workflow; external providers are not required to supply them.

## 014 — Vulnerability Register custom fields
Definitions are administrator-managed and have stable generated keys, display name, required flag, table-visibility flag and order. Values are stored as JSON per vulnerability so adding each new field does not need its own migration. Initial support uses migration 0011. Custom-field mutations require Admin; deleting a field deletes its saved values.

## 015 — Unified affected product/version presentation
Vulnerability Register and Scan Result tables show product and version in one cell, with version on a secondary line. Underlying fields remain separate in storage and record details.

## 016 — Advisory asset matching in Scan Result
Compare the original message against identifying fields in current asset inventory and useful custom asset-field values; do not maintain a duplicate hand-written keyword list. Show both a row highlight/flag and asset/term details. Matches are heuristic and must not auto-approve a finding or replace version/applicability validation. Compute against live inventory without a separate matching table or schema migration.

## 017 — Authentication and local accounts
Current source uses signed HTTP-only cookies, PBKDF2-HMAC-SHA256 password hashes and server-side protection for app pages, APIs and API docs. If the users table is empty, bootstrap admin / vulmgm for local/testing without forcing a first-login password change. This known default must be changed before untrusted-network exposure. Existing user passwords are preserved; the signing key is generated under ignored local data unless configured through VULM_SESSION_SECRET.

## 018 — Schema safety
Schema target is 11 and migration 0011 is latest. Do not edit released migrations in place, migrate without verifying DB path and a backup, or assume the 3.6.5 version bump requires a database migration.
