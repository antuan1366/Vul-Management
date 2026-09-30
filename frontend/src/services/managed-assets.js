let editingAssetId = null;
let assetFields = [];

const assetConfig = window.ASSET_CONFIG || {};

async function loadAssetFields() {
    assetFields = await apiRequest(
        `/api/asset-fields?asset_type=${encodeURIComponent(assetConfig.assetType)}`
    );
}

function getFieldValue(field, asset) {
    if (!asset) {
        return null;
    }

    if (field.system_field) {
        return asset[field.field_key] ?? null;
    }

    return asset.custom_fields?.[field.field_key] ?? null;
}

function createFieldHtml(field, value = null) {
    const required = field.required ? "required" : "";
    const escapedValue =
        value === null || value === undefined
            ? ""
            : escapeHtml(String(value));

    let inputHtml;

    switch (field.field_type) {
        case "textarea":
            inputHtml = `
                <textarea
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    rows="4"
                    ${required}
                >${escapedValue}</textarea>
            `;
            break;

        case "number":
            inputHtml = `
                <input
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    type="number"
                    value="${escapedValue}"
                    ${required}
                >
            `;
            break;

        case "date":
            inputHtml = `
                <input
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    type="date"
                    value="${escapedValue}"
                    ${required}
                >
            `;
            break;

        case "select":
        case "multiselect":
            inputHtml = `
                <select
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    ${field.field_type === "multiselect" ? "multiple" : ""}
                    ${required}
                >
                    ${field.field_type === "select" ? '<option value="">Select...</option>' : ""}
                    ${(field.options || []).map(option => `
                        <option
                            value="${escapeHtml(option)}"
                            ${
                                field.field_type === "multiselect"
                                    ? (Array.isArray(value) && value.includes(option) ? "selected" : "")
                                    : (String(value) === String(option) ? "selected" : "")
                            }
                        >
                            ${escapeHtml(option)}
                        </option>
                    `).join("")}
                </select>
            `;
            break;

        case "boolean":
            inputHtml = `
                <select
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    ${required}
                >
                    <option value="">Select...</option>
                    <option value="true" ${value === true ? "selected" : ""}>Yes</option>
                    <option value="false" ${value === false ? "selected" : ""}>No</option>
                </select>
            `;
            break;

        default:
            inputHtml = `
                <input
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    type="${field.field_type === "email" ? "email" : field.field_type === "url" ? "url" : "text"}"
                    value="${escapedValue}"
                    ${required}
                >
            `;
    }

    return `
        <div class="form-field">
            <label for="field_${field.field_key}">
                ${escapeHtml(field.label)}${field.required ? " *" : ""}
            </label>
            ${inputHtml}
        </div>
    `;
}

function renderAssetForm(asset = null) {
    const container = document.getElementById("asset-dynamic-fields");

    if (!container) {
        return;
    }

    container.innerHTML = assetFields
        .filter(field => field.visible)
        .map(field => createFieldHtml(field, getFieldValue(field, asset)))
        .join("");
}

async function loadAssets() {
    const tableBody = document.getElementById("assets-table-body");
    const count = document.getElementById("asset-count");

    if (!tableBody) {
        return;
    }

    tableBody.innerHTML = `
        <tr>
            <td colspan="8" class="loading-cell">Loading ${escapeHtml(assetConfig.pluralLabel.toLowerCase())}...</td>
        </tr>
    `;

    try {
        const assets = await apiRequest(assetConfig.endpoint);

        if (count) {
            count.textContent = `${assets.length} ${assets.length === 1 ? "Asset" : "Assets"}`;
        }

        if (assets.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-cell">
                        No ${escapeHtml(assetConfig.pluralLabel.toLowerCase())} available.
                    </td>
                </tr>
            `;
            return;
        }

        const primaryFields = assetFields
            .filter(field => field.visible)
            .slice(0, 6);

        tableBody.innerHTML = assets.map((asset, index) => {
            const cells = primaryFields.map(field => {
                const value = getFieldValue(field, asset);

                return `
                    <td>${escapeHtml(
                        Array.isArray(value) ? value.join(", ") : (value ?? "-")
                    )}</td>
                `;
            }).join("");

            return `
                <tr>
                    <td>${index + 1}</td>
                    ${cells}
                    <td>
                        <div class="table-actions">
                            <button type="button" class="secondary-button small-button" onclick="editAsset(${asset.id})">Edit</button>
                            <button type="button" class="danger-button small-button" onclick="deleteAsset(${asset.id})">Delete</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (error) {
        console.error(error);

        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="error-cell">
                    Failed to load ${escapeHtml(assetConfig.pluralLabel.toLowerCase())}.
                    <br>
                    ${escapeHtml(error.message)}
                </td>
            </tr>
        `;
    }
}

function openAssetForm() {
    editingAssetId = null;

    document.getElementById("asset-form-title").textContent =
        `Add ${assetConfig.singularLabel}`;

    renderAssetForm();

    const modal = document.getElementById("asset-form-container");
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");

    setTimeout(() => {
        modal.querySelector("input, select, textarea")?.focus();
    }, 50);
}

function closeAssetForm() {
    const modal = document.getElementById("asset-form-container");

    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");

    editingAssetId = null;

    document.getElementById("asset-form")?.reset();
}

async function editAsset(id) {
    try {
        const asset = await apiRequest(`${assetConfig.endpoint}/${id}`);

        editingAssetId = id;

        document.getElementById("asset-form-title").textContent =
            `Edit ${assetConfig.singularLabel}`;

        renderAssetForm(asset);

        const modal = document.getElementById("asset-form-container");
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");

        setTimeout(() => {
            modal.querySelector("input, select, textarea")?.focus();
        }, 50);
    } catch (error) {
        console.error(error);
        alert(`Failed to load ${assetConfig.singularLabel.toLowerCase()}.\n\n${error.message}`);
    }
}

function collectFormData() {
    const data = {};
    const customFields = {};

    for (const field of assetFields) {
        if (!field.visible) {
            continue;
        }

        const element = document.getElementById(`field_${field.field_key}`);

        if (!element) {
            continue;
        }

        let value;

        if (field.field_type === "multiselect") {
            value = Array.from(element.selectedOptions).map(option => option.value);
        } else {
            value = element.value.trim();
        }

        if (value === "" || (Array.isArray(value) && value.length === 0)) {
            value = null;
        }

        if (field.system_field) {
            data[field.field_key] = value;
        } else {
            customFields[field.field_key] = value;
        }
    }

    data.custom_fields = customFields;
    return data;
}

async function saveAsset(event) {
    event.preventDefault();

    try {
        const data = collectFormData();

        await apiRequest(
            editingAssetId === null
                ? assetConfig.endpoint
                : `${assetConfig.endpoint}/${editingAssetId}`,
            {
                method: editingAssetId === null ? "POST" : "PUT",
                body: JSON.stringify(data)
            }
        );

        closeAssetForm();
        await loadAssets();
    } catch (error) {
        console.error(error);
        alert(`Failed to save ${assetConfig.singularLabel.toLowerCase()}.\n\n${error.message}`);
    }
}

async function deleteAsset(id) {
    if (!confirm(`Are you sure you want to delete this ${assetConfig.singularLabel.toLowerCase()}?`)) {
        return;
    }

    try {
        await apiRequest(`${assetConfig.endpoint}/${id}`, {
            method: "DELETE"
        });

        await loadAssets();
    } catch (error) {
        console.error(error);
        alert(`Failed to delete ${assetConfig.singularLabel.toLowerCase()}.\n\n${error.message}`);
    }
}

function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = value ?? "";
    return element.innerHTML;
}

document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("add-asset-button");
    const cancelButton = document.getElementById("cancel-asset-button");
    const closeButton = document.getElementById("close-asset-modal");
    const modal = document.getElementById("asset-form-container");
    const form = document.getElementById("asset-form");

    addButton?.addEventListener("click", openAssetForm);
    cancelButton?.addEventListener("click", closeAssetForm);
    closeButton?.addEventListener("click", closeAssetForm);

    modal?.addEventListener("click", event => {
        if (event.target === modal) {
            closeAssetForm();
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && modal?.classList.contains("is-open")) {
            closeAssetForm();
        }
    });

    form?.addEventListener("submit", saveAsset);

    (async () => {
        try {
            await loadAssetFields();
            await loadAssets();
        } catch (error) {
            console.error(`Failed to initialize ${assetConfig.assetType} page:`, error);
        }
    })();
});
