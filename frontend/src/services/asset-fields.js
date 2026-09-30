let editingFieldId = null;


let currentFields = [];


async function loadAssetFields() {

    const tableBody =
        document.getElementById(
            "fields-table-body"
        );


    if (!tableBody) {
        return;
    }


    tableBody.innerHTML = `
        <tr>

            <td
                colspan="6"
                class="loading-cell"
            >
                Loading fields...
            </td>

        </tr>
    `;


    try {

        currentFields =
            await apiRequest(
                "/api/asset-fields?asset_type=equipment"
            );

        const fieldCount = document.getElementById("field-count");
        if (fieldCount) {
            fieldCount.textContent = currentFields.length + (currentFields.length === 1 ? " Field" : " Fields");
        }


        if (
            currentFields.length === 0
        ) {

            tableBody.innerHTML = `
                <tr>

                    <td
                        colspan="6"
                        class="empty-cell"
                    >
                        No fields configured.
                    </td>

                </tr>
            `;

            return;
        }


        tableBody.innerHTML =
            currentFields
                .map(
                    (field, fieldIndex) => {

                        return `
                            <tr>

                                <td>${fieldIndex + 1}</td>

                                <td>
                                    ${escapeHtml(
                                        field.label
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        field.field_key
                                    )}
                                </td>

                                <td>
                                    ${
                                        field.required
                                            ? "Yes"
                                            : "No"
                                    }
                                </td>

                                <td>
                                    ${
                                        field.visible
                                            ? "Yes"
                                            : "No"
                                    }
                                </td>

                                <td>
                                    ${
                                        field.system_field
                                            ? "Yes"
                                            : "No"
                                    }
                                </td>

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
                        `;

                    }
                )
                .join("");


    } catch (error) {

        console.error(error);


        tableBody.innerHTML = `
            <tr>

                <td
                    colspan="6"
                    class="error-cell"
                >

                    Failed to load fields.

                    <br>

                    ${escapeHtml(
                        error.message
                    )}

                </td>

            </tr>
        `;

    }

}


function openFieldForm() {

    editingFieldId = null;


    document.getElementById(
        "field-form-title"
    ).textContent =
        "Add Custom Field";


    const form =
        document.getElementById(
            "field-form"
        );


    form.reset();


    document.getElementById(
        "field_key"
    ).disabled = false;


    document.getElementById(
        "field_visible"
    ).checked = true;


    document.getElementById(
        "field-form-container"
    ).style.display =
        "block";


    document.getElementById(
        "field-form-container"
    ).scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


function closeFieldForm() {

    editingFieldId = null;


    document.getElementById(
        "field-form-container"
    ).style.display =
        "none";


    document.getElementById(
        "field_key"
    ).disabled = false;


    document.getElementById(
        "field-form"
    ).reset();

}


function editField(id) {

    const field =
        currentFields.find(
            (item) =>
                item.id === id
        );


    if (!field) {

        alert(
            "Field not found."
        );

        return;

    }


    editingFieldId = id;


    document.getElementById(
        "field-form-title"
    ).textContent =
        `Edit Field: ${field.label}`;


    document.getElementById(
        "field_label"
    ).value =
        field.label || "";


    document.getElementById(
        "field_key"
    ).value =
        field.field_key || "";


    document.getElementById(
        "field_key"
    ).disabled = true;


document.getElementById(
        "field_required"
    ).checked =
        Boolean(
            field.required
        );


    document.getElementById(
        "field_visible"
    ).checked =
        Boolean(
            field.visible
        );


    document.getElementById(
        "field_options"
    ).value =
        (
            field.options || []
        ).join("\n");


    document.getElementById(
        "field-form-container"
    ).style.display =
        "block";


    document.getElementById(
        "field-form-container"
    ).scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


async function saveField(event) {

    event.preventDefault();


    const label =
        document.getElementById(
            "field_label"
        ).value.trim();


    const fieldKey =
        document.getElementById(
            "field_key"
        ).value.trim();


    const fieldType = "text";


    const required =
        document.getElementById(
            "field_required"
        ).checked;


    const visible =
        document.getElementById(
            "field_visible"
        ).checked;


    const options =
        document.getElementById(
            "field_options"
        ).value
            .split("\n")
            .map(
                (item) =>
                    item.trim()
            )
            .filter(
                (item) =>
                    item.length > 0
            );


    if (!label) {

        alert(
            "Field label is required."
        );

        return;

    }


    if (
        editingFieldId === null
        &&
        !fieldKey
    ) {

        alert(
            "Field key is required."
        );

        return;

    }


    try {

        if (
            editingFieldId === null
        ) {

            await apiRequest(
                "/api/asset-fields",
                {
                    method: "POST",

                    body:
                        JSON.stringify({
                            asset_type:
                                "equipment",

                            field_key:
                                fieldKey,

                            label:
                                label,

                            field_type:
                                fieldType,

                            required:
                                required,

                            visible:
                                visible,

                            options:
                                options
                        })
                }
            );

        } else {

            await apiRequest(
                `/api/asset-fields/${editingFieldId}`,
                {
                    method: "PUT",

                    body:
                        JSON.stringify({
                            label:
                                label,

                            required:
                                required,

                            visible:
                                visible,

                            options:
                                options
                        })
                }
            );

        }


        closeFieldForm();


        await loadAssetFields();


    } catch (error) {

        console.error(error);


        alert(
            `Failed to save field.\n\n${error.message}`
        );

    }

}


async function deleteField(id) {

    const field =
        currentFields.find(
            (item) =>
                item.id === id
        );


    if (!field) {
        return;
    }


    const confirmed =
        confirm(
            `Are you sure you want to delete "${field.label}"?`
        );


    if (!confirmed) {
        return;
    }


    try {

        await apiRequest(
            `/api/asset-fields/${id}`,
            {
                method: "DELETE"
            }
        );


        await loadAssetFields();


    } catch (error) {

        console.error(error);


        alert(
            `Failed to delete field.\n\n${error.message}`
        );

    }

}


function escapeHtml(value) {

    const element =
        document.createElement(
            "div"
        );


    element.textContent =
        value ?? "";


    return element.innerHTML;

}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        const addButton =
            document.getElementById(
                "add-field-button"
            );


        const cancelButton =
            document.getElementById(
                "cancel-field-button"
            );


        const form =
            document.getElementById(
                "field-form"
            );


        if (addButton) {

            addButton.addEventListener(
                "click",
                openFieldForm
            );

        }


        if (cancelButton) {

            cancelButton.addEventListener(
                "click",
                closeFieldForm
            );

        }


        if (form) {

            form.addEventListener(
                "submit",
                saveField
            );

        }


        loadAssetFields();

    }
);