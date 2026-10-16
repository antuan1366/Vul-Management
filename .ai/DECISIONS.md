# DECISIONS

## 001 — Core functionality first
The platform must operate without AI. Do not add Mem0, Gemini, hosted LLMs or local LLMs unless the user explicitly requests them.

## 002 — Modular backend
Separate API routes, business services, SQLAlchemy models, Pydantic schemas and core configuration. Business logic should not be embedded in route handlers.

## 003 — SQLite single-file database
SQLite is the current database, at `backend/data/vul_management.db`. SQLAlchemy is the data-access layer and Alembic manages schema changes. The database is local runtime state and must not be committed or casually deleted. Keep future database portability possible by isolating persistence concerns.

## 004 — Separate asset categories
Asset categories are Equipment, Operating Systems, Applications and Libraries. Use shared patterns where appropriate while preserving category-specific fields and identification behavior.

## 005 — Candidate before approval
External CVE findings and Telegram-derived candidates must remain reviewable evidence. Do not silently promote raw external findings into approved inventory without the intended administrator workflow.

## 006 — Keep external provider code isolated
NVD, OSV, CISA and Telegram integration logic belongs in dedicated services/modules, not duplicated across frontend pages or API route handlers.

## 007 — Shared frontend patterns
The sidebar, common CSS components and table preferences should be shared. The current table control label is **Table Setting**. Do not reintroduce a gear-only control or create page-specific duplicates without explicit design approval.

## 008 — AI project memory
The `.ai/` directory preserves context, architecture, state, decisions, UI rules, compatibility notes and tasks. Git history records code history; project docs must describe the current implementation and known gaps.

## 009 — Git release discipline
Develop on `develop` or feature branches. Do not merge to `main` without explicit user approval. Avoid destructive Git operations and preserve local runtime data.

## 010 — UI design system
Use a fixed dark charcoal collapsible sidebar and a light workspace with white cards, neutral borders, compact operational tables, consistent primary/secondary/danger actions and modal-based forms where appropriate. The complete design contract is `.ai/UI_STYLE_GUIDE.md`.

## 011 — Human review of threat intelligence
Public Telegram messages and external feed records are untrusted inputs. Extract CVE data, retain source context, enrich where possible, and preserve the review/approval boundary. Jira integration is a desired capability, not an implemented feature unless verified.
