(() => {
    const script = document.currentScript;
    const tableKey = script?.dataset.tableKey;
    if (!tableKey) return;

    const table = tableKey === "scan-results"
        ? document.querySelector("#results-table-body")?.closest("table")
        : tableKey === "nessus-results"
            ? document.querySelector("#nessus-results-table")
            : document.querySelector("#vulnerabilities-table");
    if (!table) return;

    const $ = (id) => document.getElementById(id);
    const defaults = { pageSize: 25, columns: {}, widths: {} };
    let settings = structuredClone(defaults);
    let currentPage = 1;
    let saveTimer = null;
    let resizeObserver = null;
    let saving = false;

    const css = document.createElement("style");
    css.textContent = `
        .table-preferences-toolbar{display:flex;align-items:center;justify-content:flex-end;gap:12px;flex-wrap:wrap;margin:0 0 12px}
        .table-preferences-toolbar.vulnerability-table-preferences-toolbar{margin:0 28px 12px 24px}
        .table-preferences-button{display:inline-flex;align-items:center;gap:7px;min-height:36px;padding:7px 11px;border:1px solid #d5d8dd;border-radius:6px;background:#fff;color:#333;font:inherit;cursor:pointer}
        .table-preferences-button:hover{background:#f5f6f8}
        .table-preferences-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:12px 0 2px;color:#555;font-size:13px}
        .table-preferences-footer.vulnerability-table-preferences-footer{margin:0 28px 14px 24px}
        .table-preferences-paging{display:flex;align-items:center;gap:8px}
        .table-preferences-paging button{padding:6px 10px;border:1px solid #d5d8dd;border-radius:5px;background:#fff;color:#333;cursor:pointer}
        .table-preferences-paging button:disabled{opacity:.45;cursor:not-allowed}
        .table-preferences-paging select{width:auto;min-width:76px;padding:6px 8px;border:1px solid #d5d8dd;border-radius:5px;background:#fff}
        .table-preferences-modal{position:fixed;inset:0;z-index:1200;display:none;align-items:center;justify-content:center;padding:20px;background:rgba(15,18,24,.45)}
        .table-preferences-modal.open{display:flex}
        .table-preferences-dialog{width:min(520px,100%);max-height:calc(100vh - 40px);overflow:auto;padding:24px;border:1px solid #ddd;border-radius:12px;background:#fff;color:#222;box-shadow:0 18px 50px rgba(0,0,0,.2)}
        .table-preferences-dialog h2{margin:0 0 6px;font-size:20px}
        .table-preferences-dialog p{margin:0 0 18px;color:#666;line-height:1.5}
        .table-preferences-dialog label{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #eee;font-weight:400}
        .table-preferences-dialog input[type=checkbox]{width:16px;height:16px;margin:0}
        .table-preferences-dialog .table-preferences-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:20px}
        .table-preferences-resize-handle{position:absolute;top:0;right:-3px;width:7px;height:100%;cursor:col-resize;user-select:none;touch-action:none}
        .table-preferences-resize-handle:hover,.table-preferences-resize-handle.dragging{background:rgba(70,90,120,.22)}
        .table-preferences-saving{font-size:12px;color:#666}
        @media(max-width:600px){.table-preferences-footer{align-items:flex-start;flex-direction:column}.table-preferences-toolbar.vulnerability-table-preferences-toolbar{margin:0 16px 12px 12px}.table-preferences-footer.vulnerability-table-preferences-footer{margin:0 16px 14px 12px}.table-preferences-dialog{padding:18px}}
    `;
    document.head.appendChild(css);

    const toolbar = document.createElement("div");
    toolbar.className = "table-preferences-toolbar" + (tableKey === "vulnerabilities" ? " vulnerability-table-preferences-toolbar" : "");
    toolbar.innerHTML = '<button type="button" class="table-preferences-button" id="open-table-preferences" aria-haspopup="dialog">Table Setting</button>';

    const footer = document.createElement("div");
    footer.className = "table-preferences-footer" + (tableKey === "vulnerabilities" ? " vulnerability-table-preferences-footer" : "");
    footer.innerHTML = '<span id="table-preferences-range">Showing 0 records</span><div class="table-preferences-paging"><label for="table-preferences-page-size" style="display:inline;padding:0;border:0">Rows per page</label><select id="table-preferences-page-size"><option value="10">10</option><option value="25">25</option><option value="50">50</option><option value="100">100</option></select><button type="button" id="table-preferences-prev">Previous</button><span id="table-preferences-page">1 / 1</span><button type="button" id="table-preferences-next">Next</button></div>';

    const modal = document.createElement("div");
    modal.className = "table-preferences-modal";
    modal.id = "table-preferences-modal";
    modal.setAttribute("aria-hidden", "true");
    modal.innerHTML = '<section class="table-preferences-dialog" role="dialog" aria-modal="true" aria-labelledby="table-preferences-title"><h2 id="table-preferences-title">Table Setting</h2><p>Choose which columns are visible. Drag the right edge of a table heading to resize its column. Settings are saved for the whole application.</p><div id="table-preferences-columns"></div><div class="table-preferences-actions"><button type="button" class="secondary-button" id="cancel-table-preferences">Cancel</button><button type="button" class="primary-button" id="save-table-preferences">Save Settings</button></div></section>';
    document.body.append(toolbar, footer, modal);

    const host = document.createElement("div");
    host.className = "table-preferences-host";
    const tableWrapper = table.parentElement;
    const hasWrapper = tableWrapper.classList.contains("table-container") || tableWrapper.classList.contains("vulnerability-table-wrap");
    // Keep controls outside the horizontally scrollable table wrapper.
    if (hasWrapper) {
        tableWrapper.parentElement.insertBefore(host, tableWrapper);
        tableWrapper.parentElement.insertBefore(footer, tableWrapper.nextSibling);
    } else {
        tableWrapper.insertBefore(host, table);
        tableWrapper.insertBefore(footer, table.nextSibling);
    }
    host.appendChild(toolbar);

    function headings() {
        return Array.from(table.querySelectorAll("thead tr:first-child th")).map((th, index) => {
            let label = (th.innerText || th.textContent || "").trim().replace(/\s+/g, " ");
            if (!label && th.querySelector("input[type=checkbox]")) label = "Selection";
            return { index, label: label || ("Column " + (index + 1)), key: th.dataset.columnKey || ("col-" + index) };
        });
    }

    function isVisible(column) {
        return settings.columns[column.key] !== false;
    }

    function applyColumns() {
        const cols = headings();
        const allRows = [table.querySelector("thead tr"), ...Array.from(table.querySelectorAll("tbody tr"))].filter(Boolean);
        cols.forEach(col => {
            allRows.forEach(row => {
                if (row.children.length === 1 && Number(row.children[0].getAttribute("colspan") || 1) > 1) {
                    row.style.display = "";
                    return;
                }
                const cell = row.children[col.index];
                if (!cell) return;
                cell.style.display = isVisible(col) ? "" : "none";
                if (settings.widths[col.key]) {
                    cell.style.width = settings.widths[col.key] + "px";
                    cell.style.minWidth = settings.widths[col.key] + "px";
                    cell.style.maxWidth = settings.widths[col.key] + "px";
                } else {
                    cell.style.width = "";
                    cell.style.minWidth = "";
                    cell.style.maxWidth = "";
                }
            });
        });
        installResizeHandles();
    }

    function dataRows() {
        return Array.from(table.querySelectorAll("tbody tr")).filter(row => {
            if (row.children.length === 1 && Number(row.children[0].getAttribute("colspan") || 1) > 1) return false;
            return true;
        });
    }

    function applyPagination() {
        const rows = dataRows();
        const total = rows.length;
        const pageSize = Number(settings.pageSize) || 25;
        const pages = Math.max(1, Math.ceil(total / pageSize));
        currentPage = Math.min(Math.max(1, currentPage), pages);
        const start = (currentPage - 1) * pageSize;
        rows.forEach((row, index) => { row.style.display = index >= start && index < start + pageSize ? "" : "none"; });
        const shownStart = total ? start + 1 : 0;
        const shownEnd = Math.min(start + pageSize, total);
        $("table-preferences-range").textContent = "Showing " + shownStart + "–" + shownEnd + " of " + total + " records";
        $("table-preferences-page").textContent = currentPage + " / " + pages;
        $("table-preferences-prev").disabled = currentPage <= 1;
        $("table-preferences-next").disabled = currentPage >= pages;
        $("table-preferences-page-size").value = String(pageSize);
    }

    function applySettings() {
        applyColumns();
        applyPagination();
    }

    function setStatus(text) {
        const status = $("table-preferences-save-status");
        if (status) status.textContent = text || "";
    }

    async function saveSettings() {
        
        try {
            await apiRequest("/api/table-preferences/" + encodeURIComponent(tableKey), {
                method: "PUT",
                body: JSON.stringify({ settings })
            });
            
        } catch (error) {
            console.error("Could not save table settings:", error);
        }
    }

    function scheduleSave() {
        window.clearTimeout(saveTimer);
        saveTimer = window.setTimeout(saveSettings, 250);
    }

    function renderColumnSettings() {
        const container = $("table-preferences-columns");
        container.innerHTML = "";
        headings().forEach(col => {
            const label = document.createElement("label");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = isVisible(col);
            checkbox.dataset.columnKey = col.key;
            const text = document.createElement("span");
            text.textContent = col.label;
            label.append(checkbox, text);
            container.appendChild(label);
        });
        $("table-preferences-page-size").value = String(settings.pageSize);
    }

    function openSettings() {
        renderColumnSettings();
        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
    }

    function closeSettings() {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
    }

    function installResizeHandles() {
        headings().forEach(col => {
            const th = table.querySelector("thead tr:first-child")?.children[col.index];
            if (!th || th.querySelector(".table-preferences-resize-handle")) return;
            th.style.position = "relative";
            const handle = document.createElement("span");
            handle.className = "table-preferences-resize-handle";
            handle.setAttribute("role", "separator");
            handle.setAttribute("aria-label", "Resize " + col.label + " column");
            handle.addEventListener("pointerdown", event => {
                event.preventDefault();
                event.stopPropagation();
                const startX = event.clientX;
                const startWidth = th.getBoundingClientRect().width;
                handle.classList.add("dragging");
                handle.setPointerCapture?.(event.pointerId);
                const move = moveEvent => {
                    const width = Math.max(60, Math.min(900, Math.round(startWidth + moveEvent.clientX - startX)));
                    settings.widths[col.key] = width;
                    applyColumns();
                    // Keep this header responsive while dragging.
                    const current = table.querySelector("thead tr:first-child")?.children[col.index];
                    if (current) {
                        current.style.width = width + "px";
                        current.style.minWidth = width + "px";
                        current.style.maxWidth = width + "px";
                    }
                };
                const end = () => {
                    handle.classList.remove("dragging");
                    window.removeEventListener("pointermove", move);
                    window.removeEventListener("pointerup", end);
                    scheduleSave();
                };
                window.addEventListener("pointermove", move);
                window.addEventListener("pointerup", end, { once: true });
            });
            th.appendChild(handle);
        });
    }

    function migrateLegacyColumnSettings(saved) {
        const layouts = {
            "scan-results": {
                0: "selection",
                1: "row-number",
                2: "scan-date",
                3: "cve",
                5: "score",
                6: "affected",
                7: "affected-version",
                8: "actions"
            },
            "vulnerabilities": {
                0: "selection",
                1: "row-number",
                2: "cve",
                4: "cvss",
                5: "affected-product",
                6: "affected-version",
                7: "mitigation",
                8: "date",
                9: "jira",
                10: "actions"
            }
        };
        const layout = layouts[tableKey];
        if (!layout) return saved;

        const originalColumns = { ...(saved?.columns || {}) };
        const originalWidths = { ...(saved?.widths || {}) };
        const allKeys = [...Object.keys(originalColumns), ...Object.keys(originalWidths)];
        const hasLegacyKeys = allKeys.some(key => /^col-\d+$/.test(key));
        if (!allKeys.length && !("columns" in (saved || {})) && !("widths" in (saved || {}))) return saved;

        const migrate = (source) => {
            const target = {};
            for (const [key, value] of Object.entries(source)) {
                if (!/^col-\d+$/.test(key)) target[key] = value;
            }
            if (hasLegacyKeys) {
                for (const [legacyIndex, stableKey] of Object.entries(layout)) {
                    const legacyKey = "col-" + legacyIndex;
                    if (Object.prototype.hasOwnProperty.call(source, legacyKey)) {
                        target[stableKey] = source[legacyKey];
                    }
                }
            }

            if (tableKey === "scan-results" && Object.prototype.hasOwnProperty.call(target, "affected-version")) {
                const affectedWasProvided = Object.prototype.hasOwnProperty.call(target, "affected");
                if (!affectedWasProvided) {
                    target.affected = target["affected-version"] !== false;
                } else {
                    target.affected = target.affected !== false || target["affected-version"] !== false;
                }
                delete target["affected-version"];
            }

            if (tableKey === "vulnerabilities") {
                const aliases = ["affected-product", "affected-version"];
                const providedAliases = aliases.filter(key => Object.prototype.hasOwnProperty.call(target, key));
                if (providedAliases.length) {
                    if (!Object.prototype.hasOwnProperty.call(target, "affected")) {
                        target.affected = providedAliases.some(key => target[key] !== false);
                    }
                    delete target["affected-product"];
                    delete target["affected-version"];
                }
            }
            return target;
        };

        const columns = migrate(originalColumns);
        const widths = migrate(originalWidths);

        // Preserve the width of the previous product field when merging product/version.
        if (tableKey === "vulnerabilities" && !Object.prototype.hasOwnProperty.call(widths, "affected")) {
            if (Object.prototype.hasOwnProperty.call(originalWidths, "affected-product")) {
                widths.affected = originalWidths["affected-product"];
            } else if (Object.prototype.hasOwnProperty.call(originalWidths, "affected-version")) {
                widths.affected = originalWidths["affected-version"];
            }
        }

        const migrated = { ...(saved || {}), columns, widths };
        return JSON.stringify(migrated) === JSON.stringify(saved || {}) ? saved : migrated;
    }

    async function loadSettings() {
        try {
            const data = await apiRequest("/api/table-preferences/" + encodeURIComponent(tableKey));
            const original = data.settings || {};
            const saved = migrateLegacyColumnSettings(original);
            settings = { ...structuredClone(defaults), ...saved, columns: { ...(saved.columns || {}) }, widths: { ...(saved.widths || {}) } };
            if (saved !== original) {
                await saveSettings();
            }
        } catch (error) {
            console.error("Could not load table settings:", error);
        }
        applySettings();
    }

    $("open-table-preferences").addEventListener("click", openSettings);
    $("cancel-table-preferences").addEventListener("click", closeSettings);
    $("save-table-preferences").addEventListener("click", () => {
        const nextColumns = {};
        $("table-preferences-columns").querySelectorAll("input[data-column-key]").forEach(input => { nextColumns[input.dataset.columnKey] = input.checked; });
        settings.columns = nextColumns;
        closeSettings();
        applySettings();
        saveSettings();
    });
    $("table-preferences-modal").addEventListener("click", event => { if (event.target === modal) closeSettings(); });
    $("table-preferences-page-size").addEventListener("change", event => {
        settings.pageSize = Number(event.target.value);
        currentPage = 1;
        applyPagination();
        scheduleSave();
    });
    $("table-preferences-prev").addEventListener("click", () => { currentPage--; applyPagination(); });
    $("table-preferences-next").addEventListener("click", () => { currentPage++; applyPagination(); });

    const body = table.querySelector("tbody");
    if (body) {
        const observer = new MutationObserver(() => {
            // Avoid resetting the current page when the underlying table refreshes.
            applySettings();
        });
        observer.observe(body, { childList: true, subtree: true });
        resizeObserver = observer;
    }

    loadSettings().then(() => {
        if (body) applySettings();
    });
})();