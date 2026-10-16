# UI Style Guide — Vul-Management

Purpose: this document is the implementation contract for any AI or developer recreating, extending, or restyling the Vul-Management interface. Read it before writing frontend code. It documents the current visual language and interaction patterns, not a license to replace existing UI wholesale.

## 1. Source of truth and conflict resolution

Inspect the current code before changing it:
- Shared navigation and active-page logic: `frontend/src/services/sidebar.js`
- Global design and component CSS: `frontend/src/styles/main.css`
- Shared table preferences/pagination/column sizing: `frontend/src/services/table-preferences.js`
- Page markup: `frontend/src/pages/*.html`
- Page-specific behavior: matching files in `frontend/src/services/`

When this guide and actual source differ, inspect both and preserve existing working behavior. Update this guide after an approved UI decision. Do not invent a second design system or introduce a framework without approval.

## 2. Product visual identity

- Product: **Vul-Management**, a practical vulnerability-management web application.
- Overall pattern: a fixed, dark charcoal left sidebar paired with a light, low-noise workspace.
- Content should feel like an operational security console: dense enough for asset and vulnerability work, but readable and restrained.
- Use neutral colors. Reserve strong red for destructive actions/errors and status meanings; do not decorate every panel with bright colors.
- Use text labels with icons where useful. Do not rely on an icon alone for an important action.
- The interface is currently plain HTML, CSS, and JavaScript served by FastAPI. Do not migrate to React/Vue or add a CSS framework as part of a routine page change.

## 3. Layout and navigation

### Sidebar
- Fixed to the left, full viewport height.
- Expanded width: approximately **250px**.
- Collapsed width: approximately **64px**.
- Dark background: approximately `#17191d`; borders/dividers: `#292c31`.
- Brand header height: approximately **68px**.
- The brand mark is a compact square with a single “V”; brand text is “Vul-Management” with “Vulnerability Platform” below.
- Sidebar sections are collapsible; the current page is marked active.
- Menu labels currently implemented in `sidebar.js`:
  - Dashboard
  - Assets → Equipment, Operating Systems, Applications, Libraries
  - Threat Intelligence → Vulnerability Scan, Scan Result, Vulnerability Register
  - Reporting → placeholder Dashboard and Reports
  - Administration → Vulnerability Feeds, Telegram Feeds, Telegram Settings, Logs & Events
- Product naming requirement to reconcile: the intended nested label is **Vulnerabilities** rather than **Vulnerability Register**. Do not silently change the route/file name when only changing a label; update documentation and verify active navigation.
- The CISA KEV and standalone NVD navigation items should not be added as separate sidebar entries.
- Main content begins to the right of the sidebar. `.page-container` uses a maximum width around **1600px**, **32px** padding, and a left margin matching the expanded/collapsed sidebar.
- The legacy `.app-header` is hidden; do not add a second top navigation bar unless explicitly requested.

## 4. Typography and spacing

- Base font: Arial, sans-serif; base body size around **14px**.
- Primary page heading: around **28px**, weight 600, line-height 1.25.
- Section heading: around **20px**.
- Body and form labels: around **14px**; helper text, metadata and compact statuses may use **12–13px**.
- Use a consistent spacing rhythm: 6–12px for control gaps, 14–20px inside cards/sections, and around 24–32px between major page regions.
- Keep headings and descriptions left-aligned. Avoid oversized hero sections and marketing-style layouts.

## 5. Colors, surfaces and borders

Existing CSS is primarily literal values rather than centralized design tokens. Preserve the established palette:
- Workspace background: `#f5f6f8`
- Main text: `#222`
- Secondary text: `#666`
- Sidebar background: `#17191d`
- Sidebar hover: `#24272c`
- Sidebar selected item: `#30343b`
- Light borders: typically `#ddd` or `#d5d8dd`
- Primary button: charcoal `#222` with white text
- Secondary button: light gray `#e9eaed` with dark text
- Danger button/error: `#b42318`
- Cards/dialogs: white, subtle gray border, moderate rounded corners.

Prefer 1px borders and restrained shadows. Do not introduce gradients, glassmorphism, neon colors, or a fully dark content area without explicit approval.

## 6. Page structure

Typical page:
1. `.page-container`
2. `.page-header` with title/description on the left and page actions on the right
3. Optional status/progress area
4. One or more `.content-card` sections
5. `.section-header` with section title/description and item count or actions
6. `.table-container` around wide tables
7. Modal markup at page level when create/edit/review dialogs are needed

Use `.dashboard-card` and `.dashboard-grid` for dashboard metrics. Avoid nesting too many cards. A page should prioritize its primary task and keep secondary settings out of the way.

## 7. Buttons and controls

- Primary action: `.primary-button`, charcoal background and white text.
- Secondary/cancel action: `.secondary-button`, light-gray background.
- Destructive action: `.danger-button`, red background.
- Compact table action: `.small-button` when supported by existing CSS.
- Use clear verbs: Add, Save, Cancel, Scan, Approve, Reject, Delete.
- Align related actions in a flex row using `.table-actions`, `.form-actions`, or a page-specific toolbar.
- Inputs, selects and textareas should fill their form field, have consistent padding, a subtle border, rounded corners, and a visible focus border.
- Do not disable browser focus indicators without replacing them with a visible alternative.
- Destructive or state-changing actions should have a clear label and appropriate confirmation when data loss is possible.

## 8. Tables and Table Setting

Tables are a core part of the product and must remain practical for large operational datasets.
- Wrap tables in `.table-container` or an existing specialized wrapper with horizontal overflow.
- Use collapsed borders, left-aligned cells, light row separators and a subtle header background (around `#f8f8f8`).
- Typical cell padding is **12px**; keep headings and values compact and readable.
- Include a row-number column (`#`) and a record count when appropriate.
- Use an Actions column for row operations. Keep action buttons grouped and aligned.
- Long summaries should not force the table to become excessively wide; truncate in the cell and expose full text with a title/tooltip or a detail dialog where appropriate.
- On supported tables, the shared `table-preferences.js` service adds the exact button label **Table Setting**. Do not change it back to a gear-only control or plural “Table Settings” unless explicitly requested.
- The Table Setting dialog lets users show/hide columns. Column edges can be dragged to resize columns. Settings are saved for the whole application.
- Pagination controls show the displayed record range, rows-per-page selector, Previous/Next and current page. Supported page sizes are 10, 25, 50 and 100.
- Keep the Table Setting toolbar and pagination outside horizontally scrollable table wrappers so they remain usable.
- Do not attach the table preferences service to a table unless the page supplies the expected `data-table-key` and table/body selectors. Inspect the service before changing page integration.

## 9. Forms and dialogs

- Use existing `.modal-overlay` and `.modal-dialog` patterns for add/edit workflows rather than inline forms when the page already follows the modal pattern.
- Dialogs should have a title, short explanation if useful, a close button, labelled controls and explicit Save/Cancel actions.
- Standard form layout: `.form-grid` with two columns and a consistent gap; use `.form-full-width` for fields spanning the grid.
- Field labels must be programmatically associated with controls via `for`/matching `id`.
- Keep validation messages close to the relevant control or in a clearly visible status area.
- For review dialogs with long vulnerability/message content, prioritize readable line wrapping and a responsive single-column layout on narrow screens.
- Avoid duplicating the same action in both the page and the modal without a clear reason.

## 10. Status, review and progress

- Status text must be explicit; color alone is not enough.
- Vulnerability candidates use a review workflow; a discovered item is not automatically approved.
- Progress panels should state what is running, current status, and useful progress/details. Use `aria-live` for dynamically updated status where appropriate.
- Error text uses a restrained red treatment; loading/empty states should explain what is happening or what the user can do next.
- Keep operational status near the task that owns it instead of adding a separate global page for every background operation.

## 11. Responsive behavior and accessibility

- Sidebar collapse is supported and should remain functional.
- Wide tables scroll horizontally instead of breaking the page layout.
- At narrow widths, stack page-header content and form grids; dialogs should fit within the viewport and scroll internally if necessary.
- Use semantic buttons for actions and anchors for navigation.
- Provide accessible names for icon-only controls, proper dialog roles/labels, visible keyboard focus, and status announcements for asynchronous operations.
- Do not use color as the only signal for active, pending, approved, rejected, success or failure.

## 12. JavaScript and CSS implementation rules

- Keep page markup in `frontend/src/pages/`, shared navigation in `frontend/src/services/sidebar.js`, reusable behavior in focused service files, and shared styles in `frontend/src/styles/main.css`.
- Follow the existing plain JavaScript pattern and use the backend API through the shared API service where appropriate.
- Avoid giant page scripts and avoid copying shared sidebar/table behavior into individual pages.
- Prefer existing CSS classes before creating new ones. Keep page-specific styles scoped with clear prefixes.
- Do not overwrite the global stylesheet for a page-specific visual fix.
- Do not remove working interactions, API calls, modal IDs, table IDs, script ordering or data attributes while restyling.
- If a shared component changes, inspect every page that uses it.
- Test at minimum: page loads, navigation active state, main action, table empty/loading/error states, modal open/close/save, and narrow viewport layout.

## 13. Recreate the UI from scratch: required sequence

If rebuilding the frontend from repository documentation:
1. Read `.ai/START_HERE.md`, `.ai/PROJECT.md`, `.ai/ARCHITECTURE.md`, `.ai/PROJECT_MAP.md` and this guide.
2. Inspect the existing page list and backend routes before defining pages or API contracts.
3. Implement the shared stylesheet and sidebar first.
4. Implement common page/header/card/table/form/modal patterns.
5. Implement one page at a time, keeping each page's API/service behavior separate.
6. Implement the Table Setting/pagination behavior from the existing service contract.
7. Wire real backend endpoints; do not fabricate static sample data as production behavior.
8. Preserve SQLite/Alembic data contracts and all runtime data.
9. Run the app and verify every page and primary workflow before claiming completion.
10. Update `.ai/STATE.md`, `.ai/SESSION.md`, `.ai/TODO.md` and this guide after material changes.

## 14. Current implementation caveats

This guide is a design and behavior contract, not proof that every planned feature is complete. Verify actual code and endpoints. In particular, Jira issue creation is a product goal mentioned by the project owner; do not describe it as implemented until the integration exists and has been tested.
