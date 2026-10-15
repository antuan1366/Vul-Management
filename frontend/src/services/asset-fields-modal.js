(() => {
    const labels = {
        equipment: "Equipment",
        operating_system: "Operating Systems",
        application: "Applications",
        library: "Libraries"
    };
    let assetType = "";
    let fields = [];
    let editingId = null;

    const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[char]));

    function modalMarkup() {
        if (document.getElementById("asset-fields-manager-modal")) return;
        const wrapper = document.createElement("div");
        wrapper.innerHTML = `
            <div id="asset-fields-manager-modal" class="modal-overlay asset-fields-manager-overlay" aria-hidden="true">
                <section class="modal-dialog asset-fields-manager-dialog" role="dialog" aria-modal="true" aria-labelledby="asset-fields-manager-title">
                    <div class="modal-header">
                        <div><h2 id="asset-fields-manager-title">Manage Fields</h2><p id="asset-fields-manager-description" class="section-description"></p></div>
                        <button type="button" class="modal-close-button" data-close-manager aria-label="Close">&times;</button>
                    </div>
                    <div class="section-header asset-fields-manager-toolbar">
                        <p class="section-description">Changes apply only to this asset type.</p>
                        <button type="button" class="primary-button" id="manager-add-field">Add Custom Field</button>
                    </div>
                    <p id="manager-fields-message" class="section-description" role="status"></p>
                    <div class="table-container"><table>
                        <thead><tr><th>#</th><th>Field Name</th><th>Key</th><th>Required</th><th>Visible</th><th>System</th><th>Actions</th></tr></thead>
                        <tbody id="manager-fields-body"><tr><td colspan="7">Loading fields…</td></tr></tbody>
                    </table></div>
                </section>
            </div>
            <div id="asset-field-editor-modal" class="modal-overlay asset-field-editor-overlay" aria-hidden="true">
                <section class="modal-dialog asset-field-editor-dialog" role="dialog" aria-modal="true" aria-labelledby="manager-field-editor-title">
                    <div class="modal-header">
                        <div><h2 id="manager-field-editor-title">Add Custom Field</h2><p class="section-description">Define the field name and its behavior.</p></div>
                        <button type="button" class="modal-close-button" data-close-editor aria-label="Close">&times;</button>
                    </div>
                    <form id="manager-field-form">
                        <div class="form-grid field-form-grid">
                            <div class="form-field form-full-width"><label for="manager-field-label">Field Name *</label><input id="manager-field-label" required maxlength="120" placeholder="Example: Rack Number"></div>
                            <div class="field-checkbox-group">
                                <label class="checkbox-card"><input id="manager-field-required" type="checkbox"><span><strong>Required</strong></span></label>
                                <label class="checkbox-card"><input id="manager-field-visible" type="checkbox" checked><span><strong>Visible</strong></span></label>
                            </div>
                        </div>
                        <p id="manager-field-error" class="error-cell" role="alert"></p>
                        <div class="form-actions"><button type="submit" class="primary-button">Save Field</button><button type="button" class="secondary-button" data-close-editor>Cancel</button></div>
                    </form>
                </section>
            </div>`;
        document.body.appendChild(wrapper);
    }

    function openModal(type) {
        if (!labels[type]) return;
        assetType = type;
        modalMarkup();
        document.getElementById("asset-fields-manager-title").textContent = "Manage " + labels[type] + " Fields";
        document.getElementById("asset-fields-manager-description").textContent = "Configure the fields used by " + labels[type].toLowerCase() + ".";
        const modal = document.getElementById("asset-fields-manager-modal");
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        loadFields();
    }

    function closeManager() {
        const modal = document.getElementById("asset-fields-manager-modal");
        if (modal) {
            modal.classList.remove("is-open");
            modal.setAttribute("aria-hidden", "true");
        }
        closeEditor();
    }

    function openEditor(field = null) {
        editingId = field ? field.id : null;
        document.getElementById("manager-field-editor-title").textContent = field ? "Edit Custom Field" : "Add Custom Field";
        document.getElementById("manager-field-label").value = field?.label || "";
        document.getElementById("manager-field-required").checked = Boolean(field?.required);
        document.getElementById("manager-field-visible").checked = field ? Boolean(field.visible) : true;
        document.getElementById("manager-field-error").textContent = "";
        const modal = document.getElementById("asset-field-editor-modal");
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.getElementById("manager-field-label").focus();
    }

    function closeEditor() {
        const modal = document.getElementById("asset-field-editor-modal");
        if (!modal) return;
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.getElementById("manager-field-form")?.reset();
        editingId = null;
    }

    async function loadFields() {
        const body = document.getElementById("manager-fields-body");
        const message = document.getElementById("manager-fields-message");
        body.innerHTML = '<tr><td colspan="7">Loading fields…</td></tr>';
        message.textContent = "";
        try {
            fields = await apiRequest("/api/asset-fields?asset_type=" + encodeURIComponent(assetType));
            if (!fields.length) {
                body.innerHTML = '<tr><td colspan="7" class="empty-cell">No fields configured.</td></tr>';
                return;
            }
            body.innerHTML = fields.map((field, index) => `<tr>
                <td>${index + 1}</td><td>${esc(field.label)}</td><td>${esc(field.field_key)}</td>
                <td>${field.required ? "Yes" : "No"}</td><td>${field.visible ? "Yes" : "No"}</td><td>${field.system_field ? "Yes" : "No"}</td>
                <td><div class="table-actions">
                    ${field.editable ? '<button type="button" class="secondary-button small-button" data-field-edit="' + field.id + '">Edit</button>' : ""}
                    ${field.deletable ? '<button type="button" class="danger-button small-button" data-field-delete="' + field.id + '">Delete</button>' : ""}
                </div></td></tr>`).join("");
        } catch (error) {
            body.innerHTML = '<tr><td colspan="7" class="error-cell">' + esc(error.message || "Failed to load fields.") + '</td></tr>';
        }
    }

    async function saveField(event) {
        event.preventDefault();
        const label = document.getElementById("manager-field-label").value.trim();
        if (!label) return;
        const payload = {
            label,
            required: document.getElementById("manager-field-required").checked,
            visible: document.getElementById("manager-field-visible").checked
        };
        try {
            if (editingId === null) {
                await apiRequest("/api/asset-fields", { method: "POST", body: JSON.stringify({ ...payload, asset_type: assetType }) });
            } else {
                await apiRequest("/api/asset-fields/" + editingId, { method: "PUT", body: JSON.stringify(payload) });
            }
            closeEditor();
            await loadFields();
            document.getElementById("manager-fields-message").textContent = "Field saved.";
        } catch (error) {
            document.getElementById("manager-field-error").textContent = error.message || "Failed to save field.";
        }
    }

    async function deleteField(id) {
        const field = fields.find(item => item.id === id);
        if (!field || !confirm('Delete the field "' + field.label + '"?')) return;
        try {
            await apiRequest("/api/asset-fields/" + id, { method: "DELETE" });
            await loadFields();
            document.getElementById("manager-fields-message").textContent = "Field deleted.";
        } catch (error) {
            document.getElementById("manager-fields-message").textContent = error.message || "Failed to delete field.";
        }
    }

    document.addEventListener("click", event => {
        const trigger = event.target.closest("[data-manage-asset-fields]");
        if (trigger) {
            event.preventDefault();
            openModal(trigger.dataset.manageAssetFields);
            return;
        }
        const edit = event.target.closest("[data-field-edit]");
        if (edit) {
            const field = fields.find(item => item.id === Number(edit.dataset.fieldEdit));
            if (field) openEditor(field);
            return;
        }
        const remove = event.target.closest("[data-field-delete]");
        if (remove) {
            deleteField(Number(remove.dataset.fieldDelete));
            return;
        }
        if (event.target.closest("[data-close-manager]")) closeManager();
        if (event.target.closest("[data-close-editor]")) closeEditor();
        if (event.target.id === "manager-add-field") openEditor();
        if (event.target.id === "asset-fields-manager-modal") closeManager();
        if (event.target.id === "asset-field-editor-modal") closeEditor();
    });

    document.addEventListener("submit", event => {
        if (event.target.id === "manager-field-form") saveField(event);
    });
    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            const editor = document.getElementById("asset-field-editor-modal");
            const manager = document.getElementById("asset-fields-manager-modal");
            if (editor?.classList.contains("is-open")) closeEditor();
            else if (manager?.classList.contains("is-open")) closeManager();
        }
    });
    const style = document.createElement("style");
    style.textContent = `
        .asset-fields-manager-dialog{width:min(1100px,100%);max-height:calc(100vh - 48px)}
        .asset-fields-manager-toolbar{margin:0 0 12px;align-items:center}
        .asset-fields-manager-toolbar .section-description{margin:0}
        .asset-field-editor-overlay{z-index:1010}
        .asset-field-editor-dialog{width:min(560px,100%)}
        .asset-field-editor-dialog .field-form-grid{grid-template-columns:1fr;margin-top:0}
        .asset-field-editor-dialog .form-actions{justify-content:flex-end}
        .asset-field-editor-dialog .error-cell{padding:6px;text-align:left}
        @media(max-width:700px){.asset-fields-manager-dialog{padding:16px}.asset-fields-manager-toolbar{align-items:flex-start;flex-direction:column}}
    `;
    document.head.appendChild(style);
})();