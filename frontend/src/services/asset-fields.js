let editingFieldId = null;
let currentFields = [];

async function loadAssetFields() {
    const tableBody = document.getElementById("fields-table-body");

    if (!tableBody) {
        return;
    }

    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="loading-cell">Loading fields...</td>
        </tr>
    `;

    try {
        currentFields = await apiRequest(
            "/api/asset-fields?asset_type=equipment"
        );

        const fieldCount = document.getElementById("field-count");

        if (fieldCount) {
            fieldCount.textContent =
                currentFields.length +
                (currentFields.length === 1 ? " Field" : " Fields");
        }

        if (currentFields.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-cell">
                        No fields configured.
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = currentFields.map(
            (field, fieldIndex) => `
                <tr>
                    <td>${fieldIndex + 1}</td>
                    <td>${escapeHtml(field.label)}</td>
                    <td>${escapeHtml(field.field_key)}</td>
                    <td>${field.required ? "Yes" : "No"}</td>
                    <td>${field.visible ? "Yes" : "No"}</td>
                    <td>${field.system_field ? "Yes" : "No"}</td>
                    <td>
                        <div class="table-actions">
                            ${
                                field.editable
                                    ? `
                                        <button
                                            type="button"
                                            class="secondary-button small-button"
                                            onclick="editField(${field.id})"
                                        >
                                            Edit
                                        </button>
                                    `
                                    : ""
                            }
                            ${
                                field.deletable
                                    ? `
                                        <button
                                            type="button"
                                            class="danger-button small-button"
                                            onclick="deleteField(${field.id})"
                                        >
                                            Delete
                                        </button>
                                    `
                                    : ""
                            }
                        </div>
                    </td>
                </tr>
            `
        ).join("");
    } catch (error) {
        console.error(error);

        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="error-cell">
                    Failed to load fields.
                    <br>
                    ${escapeHtml(error.message)}
                </td>
            </tr>
        `;
    }
}

function openFieldModal(field = null) {
    editingFieldId = field ? field.id : null;

    document.getElementById("field-form-title").textContent =
        field ? `Edit Field: ${field.label}` : "Add Custom Field";

    document.getElementById("field_label").value =
        field?.label || "";

    document.getElementById("field_required").checked =
        Boolean(field?.required);

    document.getElementById("field_visible").checked =
        field ? Boolean(field.visible) : true;

    const modal = document.getElementById("field-modal");

    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");

    setTimeout(() => {
        document.getElementById("field_label").focus();
    }, 50);
}

function closeFieldModal() {
    editingFieldId = null;

    const modal = document.getElementById("field-modal");

    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");

    document.getElementById("field-form").reset();
    document.getElementById("field_visible").checked = true;
}

function editField(id) {
    const field = currentFields.find(
        (item) => item.id === id
    );

    if (!field) {
        alert("Field not found.");
        return;
    }

    openFieldModal(field);
}

async function saveField(event) {
    event.preventDefault();

    const label = document.getElementById("field_label")
        .value.trim();

    const required = document.getElementById("field_required")
        .checked;

    const visible = document.getElementById("field_visible")
        .checked;

    if (!label) {
        alert("Field name is required.");
        return;
    }

    try {
        if (editingFieldId === null) {
            await apiRequest(
                "/api/asset-fields",
                {
                    method: "POST",
                    body: JSON.stringify({
                        asset_type: "equipment",
                        label,
                        required,
                        visible
                    })
                }
            );
        } else {
            await apiRequest(
                `/api/asset-fields/${editingFieldId}`,
                {
                    method: "PUT",
                    body: JSON.stringify({
                        label,
                        required,
                        visible
                    })
                }
            );
        }

        closeFieldModal();
        await loadAssetFields();
    } catch (error) {
        console.error(error);

        alert(
            `Failed to save field.\\n\\n${error.message}`
        );
    }
}

async function deleteField(id) {
    const field = currentFields.find(
        (item) => item.id === id
    );

    if (!field) {
        return;
    }

    if (
        !confirm(
            `Are you sure you want to delete "${field.label}"?`
        )
    ) {
        return;
    }

    try {
        await apiRequest(
            `/api/asset-fields/${id}`,
            { method: "DELETE" }
        );

        await loadAssetFields();
    } catch (error) {
        console.error(error);

        alert(
            `Failed to delete field.\\n\\n${error.message}`
        );
    }
}

function escapeHtml(value) {
    const element = document.createElement("div");

    element.textContent = value ?? "";

    return element.innerHTML;
}

document.addEventListener(
    "DOMContentLoaded",
    () => {
        document.getElementById("add-field-button")
            ?.addEventListener(
                "click",
                () => openFieldModal()
            );

        document.getElementById("cancel-field-button")
            ?.addEventListener(
                "click",
                closeFieldModal
            );

        document.getElementById("close-field-modal")
            ?.addEventListener(
                "click",
                closeFieldModal
            );

        document.getElementById("field-form")
            ?.addEventListener(
                "submit",
                saveField
            );

        document.getElementById("field-modal")
            ?.addEventListener(
                "click",
                (event) => {
                    if (
                        event.target.id === "field-modal"
                    ) {
                        closeFieldModal();
                    }
                }
            );

        document.addEventListener(
            "keydown",
            (event) => {
                if (
                    event.key === "Escape" &&
                    document.getElementById("field-modal")
                        ?.classList.contains("is-open")
                ) {
                    closeFieldModal();
                }
            }
        );

        loadAssetFields();
    }
);
