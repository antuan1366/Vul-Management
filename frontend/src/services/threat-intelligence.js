(() => {
    const $ = (id) => document.getElementById(id);
    let activeId = null;
    let records = [];
    let customFieldDefinitions = [];
    let currentUser = null;
    const selected = new Set();

    function esc(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
        }[char]));
    }

    function dt(value) {
        if (!value) return "—";
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
    }

    async function req(url, options) {
        return apiRequest(url, options);
    }

    function message(text, error = false) {
        $("vulnerability-message").textContent = text || "";
        $("vulnerability-message").classList.toggle("error", Boolean(error));
    }

    function fieldManagerMessage(text, error = false) {
        const element = $("custom-field-manager-message");
        element.textContent = text || "";
        element.classList.toggle("error", Boolean(error));
    }

    function visibleCustomFields() {
        return customFieldDefinitions.filter(field => field.show_in_table);
    }

    function renderCustomFieldHeaders() {
        const headerRow = $("vulnerabilities-table").querySelector("thead tr");
        if (!headerRow) return;
        headerRow.querySelectorAll("[data-custom-field-header]").forEach(header => header.remove());

        const actionsHeader = headerRow.querySelector('[data-column-key="actions"]');
        for (const field of visibleCustomFields()) {
            const header = document.createElement("th");
            header.dataset.columnKey = "custom-" + field.field_key;
            header.dataset.customFieldHeader = "true";
            header.textContent = field.name;
            if (actionsHeader) headerRow.insertBefore(header, actionsHeader);
            else headerRow.appendChild(header);
        }
    }

    function renderCustomFieldInputs(values = {}) {
        const container = $("vulnerability-custom-field-inputs");
        if (!container) return;
        container.innerHTML = customFieldDefinitions.map(field => {
            const inputId = "custom-vulnerability-field-" + field.field_key;
            const requiredMark = field.is_required ? " *" : "";
            return '<div class="form-field custom-field-input">' +
                '<label for="' + esc(inputId) + '">' + esc(field.name) + esc(requiredMark) + '</label>' +
                '<input id="' + esc(inputId) + '" type="text" maxlength="5000" data-custom-field-key="' + esc(field.field_key) + '"' +
                (field.is_required ? " required" : "") +
                ' value="' + esc(values[field.field_key] ?? "") + '">' +
                '</div>';
        }).join("");
    }

    function renderCustomFieldManager() {
        const container = $("custom-field-manager-list");
        if (!customFieldDefinitions.length) {
            container.innerHTML = '<div class="custom-field-manager-empty">No custom fields have been created yet.</div>';
            return;
        }

        container.innerHTML = customFieldDefinitions.map(field =>
            '<form class="custom-field-editor" data-field-id="' + field.id + '">' +
                '<div class="form-field">' +
                    '<label>Field name</label>' +
                    '<input type="text" data-field-name maxlength="100" value="' + esc(field.name) + '" required>' +
                '</div>' +
                '<div class="custom-field-editor-options">' +
                    '<label><input type="checkbox" data-field-required ' + (field.is_required ? "checked" : "") + '> Required</label>' +
                    '<label><input type="checkbox" data-field-show-in-table ' + (field.show_in_table ? "checked" : "") + '> Show in table</label>' +
                '</div>' +
                '<button class="secondary-button small-button" type="submit">Save</button>' +
                '<button class="danger-button small-button" type="button" data-delete-field="' + field.id + '">Delete</button>' +
            '</form>'
        ).join("");
    }

    async function loadCustomFields() {
        const result = await req("/api/threat-intelligence/intelligence/custom-fields");
        customFieldDefinitions = result.items || [];
        renderCustomFieldHeaders();
        renderCustomFieldInputs();
        return customFieldDefinitions;
    }

    function combinedAffected(product, version) {
        const productText = product || "Data not found in NVD";
        const versionText = version || "Not specified";
        return {
            title: productText + " | Version: " + versionText,
            html: '<div class="vulnerability-text-cell affected-combined" title="' + esc(productText + " | Version: " + versionText) + '">' +
                '<strong>' + esc(productText) + '</strong>' +
                '<small>Version: ' + esc(versionText) + '</small>' +
            '</div>'
        };
    }

    async function loadRecords() {
        const query = $("vulnerability-search").value.trim();
        const data = await req("/api/threat-intelligence/intelligence?q=" + encodeURIComponent(query) + "&limit=500");
        records = (data.items || []).sort((a, b) =>
            new Date(b.date || b.created_at || 0) - new Date(a.date || a.created_at || 0) ||
            Number(b.id || 0) - Number(a.id || 0)
        );

        const fields = visibleCustomFields();
        renderCustomFieldHeaders();
        const total = data.total ?? records.length;
        $("vulnerability-count").textContent = total + " " + (total === 1 ? "Vulnerability" : "Vulnerabilities");

        $("vulnerabilities-table-body").innerHTML = records.map((record, index) => {
            const affected = combinedAffected(record.affected_product, record.affected_versions);
            const customCells = fields.map(field => {
                const value = record.custom_fields?.[field.field_key] || "";
                return '<td><span class="vulnerability-text-cell custom-field-cell" title="' + esc(value || "—") + '">' + esc(value || "—") + '</span></td>';
            }).join("");
            const jiraCell = record.jira_issue_url
                ? '<a href="' + esc(record.jira_issue_url) + '" target="_blank" rel="noopener">' + esc(record.jira_issue_key || "Open Jira") + '</a>'
                : esc(record.jira_status || "Not sent");
            return '<tr>' +
                '<td><input class="vulnerability-row-select" type="checkbox" data-id="' + record.id + '" aria-label="Select ' + esc(record.cve_id) + '" ' + (selected.has(record.id) ? "checked" : "") + '></td>' +
                '<td>' + (index + 1) + '</td>' +
                '<td><strong>' + esc(record.cve_id) + '</strong></td>' +
                '<td>' + esc(record.cvss_score ?? "—") + '</td>' +
                '<td>' + affected.html + '</td>' +
                '<td><span class="vulnerability-text-cell" title="' + esc(record.mitigation || "No mitigation recorded") + '">' + esc(record.mitigation || "Not recorded") + '</span></td>' +
                '<td>' + esc(dt(record.date)) + '</td>' +
                '<td>' + jiraCell + '</td>' +
                customCells +
                '<td><div class="vulnerability-actions">' +
                    '<button class="secondary-button small-button" data-action="edit" data-id="' + record.id + '">Edit</button>' +
                    (record.jira_issue_key ? "" : '<button class="primary-button small-button" data-action="jira" data-id="' + record.id + '">Create Jira</button>') +
                '</div></td>' +
            '</tr>';
        }).join("") || '<tr><td class="vulnerability-table-empty" colspan="' + (9 + fields.length) + '">No vulnerabilities yet. Accept a finding in Scan Result or select Add Vulnerability.</td></tr>';

        const visibleIds = records.map(record => record.id);
        const selectAll = $("select-all-vulnerabilities");
        selectAll.checked = visibleIds.length > 0 && visibleIds.every(id => selected.has(id));
        selectAll.indeterminate = visibleIds.some(id => selected.has(id)) && !selectAll.checked;
        $("delete-selected-vulnerabilities").disabled = selected.size === 0;
        $("delete-selected-vulnerabilities").textContent = selected.size ? "Delete Selected (" + selected.size + ")" : "Delete Selected";
    }

    function resetForm() {
        activeId = null;
        $("vulnerability-form").reset();
        $("vul-cve-id").disabled = false;
        $("vulnerability-modal-title").textContent = "Add Vulnerability";
        $("vulnerability-modal-description").textContent = "Enter the CVE details and available remediation information.";
        $("save-vulnerability-button").textContent = "Save Vulnerability";
        $("vulnerability-form-message").textContent = "";
        renderCustomFieldInputs();
    }

    function openModal(record = null) {
        resetForm();
        if (record) {
            activeId = record.id;
            $("vulnerability-modal-title").textContent = "Edit Vulnerability";
            $("vulnerability-modal-description").textContent = "Update vulnerability details for " + record.cve_id + ".";
            $("save-vulnerability-button").textContent = "Save Changes";
            $("vul-cve-id").value = record.cve_id;
            $("vul-cve-id").disabled = true;
            $("vul-severity").value = record.severity || "";
            $("vul-cvss").value = record.cvss_score ?? "";
            $("vul-product").value = record.affected_product || "";
            $("vul-versions").value = record.affected_versions || "";
            $("vul-remediation").value = record.remediation || "";
            $("vul-mitigation").value = record.mitigation || "";
            $("vul-description").value = record.description || "";
            $("vul-references").value = record.references_text || "";
            renderCustomFieldInputs(record.custom_fields || {});
        }
        $("vulnerability-modal").classList.add("is-open");
        $("vulnerability-modal").setAttribute("aria-hidden", "false");
    }

    function closeModal() {
        $("vulnerability-modal").classList.remove("is-open");
        $("vulnerability-modal").setAttribute("aria-hidden", "true");
        activeId = null;
    }

    function formPayload() {
        const customFields = {};
        document.querySelectorAll("#vulnerability-custom-field-inputs [data-custom-field-key]").forEach(input => {
            customFields[input.dataset.customFieldKey] = input.value.trim() || null;
        });
        return {
            cve_id: $("vul-cve-id").value.trim().toUpperCase(),
            severity: $("vul-severity").value.trim() || null,
            cvss_score: $("vul-cvss").value === "" ? null : Number($("vul-cvss").value),
            affected_product: $("vul-product").value.trim() || null,
            affected_versions: $("vul-versions").value.trim() || null,
            remediation: $("vul-remediation").value.trim() || null,
            mitigation: $("vul-mitigation").value.trim() || null,
            description: $("vul-description").value.trim() || null,
            references_text: $("vul-references").value.trim() || null,
            custom_fields: customFields
        };
    }

    async function saveRecord(event) {
        event.preventDefault();
        const button = $("save-vulnerability-button");
        button.disabled = true;
        $("vulnerability-form-message").textContent = "Saving…";
        const payload = formPayload();
        try {
            if (activeId) {
                delete payload.cve_id;
                await req("/api/threat-intelligence/intelligence/" + activeId, {
                    method: "PUT",
                    body: JSON.stringify(payload)
                });
                message("Vulnerability updated.");
            } else {
                await req("/api/threat-intelligence/intelligence", {
                    method: "POST",
                    body: JSON.stringify(payload)
                });
                message("Vulnerability added.");
            }
            closeModal();
            await loadRecords();
        } catch (error) {
            $("vulnerability-form-message").textContent = error.message || String(error);
        } finally {
            button.disabled = false;
        }
    }

    async function handleAction(action, id) {
        const record = records.find(item => item.id === id);
        if (!record) return;
        if (action === "edit") {
            openModal(record);
            return;
        }
        if (action === "jira") {
            if (!window.confirm("Create a Jira issue for " + record.cve_id + "?")) return;
            const result = await req("/api/threat-intelligence/intelligence/" + id + "/jira", { method: "POST" });
            message("Jira issue created: " + result.issue_key);
            await loadRecords();
        }
    }

    async function deleteSelected() {
        const ids = Array.from(selected);
        if (!ids.length) {
            message("Select at least one vulnerability first.", true);
            return;
        }
        const selectedRecords = records.filter(record => ids.includes(record.id));
        const jiraRecords = selectedRecords.filter(record => record.jira_issue_key);
        let warning = "Delete " + ids.length + " selected vulnerability record(s) from the Vulnerability Register? This cannot be undone.";
        if (jiraRecords.length) warning += " " + jiraRecords.length + " selected record(s) have Jira issues; deleting them here will not delete those Jira issues.";
        if (!window.confirm(warning)) return;
        let deleted = 0;
        let failed = 0;
        for (const id of ids) {
            try {
                await req("/api/threat-intelligence/intelligence/" + id, { method: "DELETE" });
                selected.delete(id);
                deleted++;
            } catch (error) {
                failed++;
            }
        }
        await loadRecords();
        message("Deleted: " + deleted + ". Failed: " + failed + ".", failed > 0);
    }

    function openCustomFieldsModal() {
        fieldManagerMessage("");
        renderCustomFieldManager();
        $("custom-fields-modal").classList.add("is-open");
        $("custom-fields-modal").setAttribute("aria-hidden", "false");
    }

    function closeCustomFieldsModal() {
        $("custom-fields-modal").classList.remove("is-open");
        $("custom-fields-modal").setAttribute("aria-hidden", "true");
    }

    async function createCustomField(event) {
        event.preventDefault();
        const button = $("create-custom-field-button");
        button.disabled = true;
        fieldManagerMessage("Creating field…");
        try {
            await req("/api/threat-intelligence/intelligence/custom-fields", {
                method: "POST",
                body: JSON.stringify({
                    name: $("new-custom-field-name").value.trim(),
                    is_required: $("new-custom-field-required").checked,
                    show_in_table: $("new-custom-field-show-in-table").checked
                })
            });
            $("custom-field-create-form").reset();
            $("new-custom-field-show-in-table").checked = true;
            await loadCustomFields();
            renderCustomFieldManager();
            await loadRecords();
            fieldManagerMessage("Custom field created.");
        } catch (error) {
            fieldManagerMessage(error.message || String(error), true);
        } finally {
            button.disabled = false;
        }
    }

    async function updateCustomField(event) {
        const form = event.target.closest(".custom-field-editor");
        if (!form) return;
        event.preventDefault();
        const fieldId = Number(form.dataset.fieldId);
        const saveButton = form.querySelector('button[type="submit"]');
        saveButton.disabled = true;
        fieldManagerMessage("Saving field…");
        try {
            await req("/api/threat-intelligence/intelligence/custom-fields/" + fieldId, {
                method: "PUT",
                body: JSON.stringify({
                    name: form.querySelector("[data-field-name]").value.trim(),
                    is_required: form.querySelector("[data-field-required]").checked,
                    show_in_table: form.querySelector("[data-field-show-in-table]").checked
                })
            });
            await loadCustomFields();
            renderCustomFieldManager();
            await loadRecords();
            fieldManagerMessage("Custom field updated.");
        } catch (error) {
            fieldManagerMessage(error.message || String(error), true);
        } finally {
            saveButton.disabled = false;
        }
    }

    async function deleteCustomField(fieldId) {
        const field = customFieldDefinitions.find(item => item.id === fieldId);
        if (!field) return;
        if (!window.confirm('Delete the custom field "' + field.name + '" and its saved values from all vulnerability records?')) return;
        fieldManagerMessage("Deleting field…");
        try {
            await req("/api/threat-intelligence/intelligence/custom-fields/" + fieldId, { method: "DELETE" });
            await loadCustomFields();
            renderCustomFieldManager();
            await loadRecords();
            fieldManagerMessage("Custom field deleted.");
        } catch (error) {
            fieldManagerMessage(error.message || String(error), true);
        }
    }

    async function initialize() {
        try {
            currentUser = await req("/api/auth/me");
        } catch (error) {
            currentUser = null;
        }
        $("manage-vulnerability-fields-button").hidden = currentUser?.role !== "admin";

        try {
            await loadCustomFields();
        } catch (error) {
            message("Could not load custom field definitions: " + (error.message || String(error)), true);
        }
        try {
            await loadRecords();
        } catch (error) {
            message(error.message || String(error), true);
        }

        $("add-vulnerability-button").addEventListener("click", () => openModal());
        $("vulnerability-search").addEventListener("input", () => loadRecords().catch(error => message(error.message, true)));
        $("delete-selected-vulnerabilities").addEventListener("click", () => deleteSelected().catch(error => message(error.message, true)));
        $("select-all-vulnerabilities").addEventListener("change", event => {
            for (const record of records) {
                if (event.target.checked) selected.add(record.id);
                else selected.delete(record.id);
            }
            document.querySelectorAll(".vulnerability-row-select").forEach(input => { input.checked = event.target.checked; });
            $("delete-selected-vulnerabilities").disabled = selected.size === 0;
            $("delete-selected-vulnerabilities").textContent = selected.size ? "Delete Selected (" + selected.size + ")" : "Delete Selected";
        });
        $("vulnerabilities-table-body").addEventListener("change", event => {
            const checkbox = event.target.closest(".vulnerability-row-select");
            if (!checkbox) return;
            const id = Number(checkbox.dataset.id);
            if (checkbox.checked) selected.add(id);
            else selected.delete(id);
            const visibleIds = records.map(record => record.id);
            const selectAll = $("select-all-vulnerabilities");
            selectAll.checked = visibleIds.length > 0 && visibleIds.every(value => selected.has(value));
            selectAll.indeterminate = visibleIds.some(value => selected.has(value)) && !selectAll.checked;
            $("delete-selected-vulnerabilities").disabled = selected.size === 0;
            $("delete-selected-vulnerabilities").textContent = selected.size ? "Delete Selected (" + selected.size + ")" : "Delete Selected";
        });
        $("vulnerabilities-table-body").addEventListener("click", event => {
            const button = event.target.closest("[data-action]");
            if (button) handleAction(button.dataset.action, Number(button.dataset.id)).catch(error => message(error.message, true));
        });
        $("vulnerability-form").addEventListener("submit", saveRecord);
        $("close-vulnerability-modal").addEventListener("click", closeModal);
        $("cancel-vulnerability-modal").addEventListener("click", closeModal);
        $("vulnerability-modal").addEventListener("click", event => { if (event.target === $("vulnerability-modal")) closeModal(); });

        $("manage-vulnerability-fields-button").addEventListener("click", () => openCustomFieldsModal());
        $("close-custom-fields-modal").addEventListener("click", closeCustomFieldsModal);
        $("close-custom-fields-modal-footer").addEventListener("click", closeCustomFieldsModal);
        $("custom-fields-modal").addEventListener("click", event => { if (event.target === $("custom-fields-modal")) closeCustomFieldsModal(); });
        $("custom-field-create-form").addEventListener("submit", createCustomField);
        $("custom-field-manager-list").addEventListener("submit", updateCustomField);
        $("custom-field-manager-list").addEventListener("click", event => {
            const button = event.target.closest("[data-delete-field]");
            if (button) deleteCustomField(Number(button.dataset.deleteField));
        });
    }

    document.addEventListener("DOMContentLoaded", initialize, { once: true });
})();
