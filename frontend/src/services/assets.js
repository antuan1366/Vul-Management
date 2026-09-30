let editingEquipmentId = null;

let equipmentFields = [];


async function loadEquipmentFields() {

    equipmentFields = await apiRequest(
        "/api/asset-fields?asset_type=equipment"
    );

}


function getFieldValue(
    field,
    equipment
) {

    if (!equipment) {
        return null;
    }


    if (field.system_field) {

        return equipment[
            field.field_key
        ] ?? null;

    }


    return (
        equipment.custom_fields?.[
            field.field_key
        ] ?? null
    );

}


function createFieldHtml(
    field,
    value = null
) {

    const requiredAttribute =
        field.required
            ? "required"
            : "";


    const escapedValue =
        value === null ||
        value === undefined
            ? ""
            : escapeHtml(
                String(value)
            );


    let inputHtml = "";


    switch (field.field_type) {

        case "textarea":

            inputHtml = `
                <textarea
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    rows="4"
                    ${requiredAttribute}
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
                    ${requiredAttribute}
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
                    ${requiredAttribute}
                >
            `;

            break;


        case "ip":

            inputHtml = `
                <input
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    type="text"
                    placeholder="192.168.1.1"
                    value="${escapedValue}"
                    ${requiredAttribute}
                >
            `;

            break;


        case "url":

            inputHtml = `
                <input
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    type="url"
                    value="${escapedValue}"
                    ${requiredAttribute}
                >
            `;

            break;


        case "email":

            inputHtml = `
                <input
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    type="email"
                    value="${escapedValue}"
                    ${requiredAttribute}
                >
            `;

            break;


        case "boolean":

            inputHtml = `
                <select
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    ${requiredAttribute}
                >

                    <option value="">
                        Select...
                    </option>

                    <option
                        value="true"
                        ${
                            value === true
                                ? "selected"
                                : ""
                        }
                    >
                        Yes
                    </option>

                    <option
                        value="false"
                        ${
                            value === false
                                ? "selected"
                                : ""
                        }
                    >
                        No
                    </option>

                </select>
            `;

            break;


        case "select":

            inputHtml = `
                <select
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    ${requiredAttribute}
                >

                    <option value="">
                        Select...
                    </option>

                    ${(field.options || [])
                        .map(
                            (option) => `
                                <option
                                    value="${escapeHtml(
                                        option
                                    )}"
                                    ${
                                        String(value) ===
                                        String(option)
                                            ? "selected"
                                            : ""
                                    }
                                >
                                    ${escapeHtml(
                                        option
                                    )}
                                </option>
                            `
                        )
                        .join("")}

                </select>
            `;

            break;


        case "multiselect":

            inputHtml = `
                <select
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    multiple
                    ${requiredAttribute}
                >

                    ${(field.options || [])
                        .map(
                            (option) => `
                                <option
                                    value="${escapeHtml(
                                        option
                                    )}"
                                    ${
                                        Array.isArray(
                                            value
                                        ) &&
                                        value.includes(
                                            option
                                        )
                                            ? "selected"
                                            : ""
                                    }
                                >
                                    ${escapeHtml(
                                        option
                                    )}
                                </option>
                            `
                        )
                        .join("")}

                </select>
            `;

            break;


        default:

            inputHtml = `
                <input
                    id="field_${field.field_key}"
                    data-field-key="${field.field_key}"
                    type="text"
                    value="${escapedValue}"
                    ${requiredAttribute}
                >
            `;

            break;

    }


    return `
        <div class="form-field">

            <label
                for="field_${field.field_key}"
            >

                ${escapeHtml(
                    field.label
                )}

                ${
                    field.required
                        ? " *"
                        : ""
                }

            </label>

            ${inputHtml}

        </div>
    `;

}


function renderEquipmentForm(
    equipment = null
) {

    const container =
        document.getElementById(
            "equipment-dynamic-fields"
        );


    if (!container) {
        return;
    }


    const visibleFields =
        equipmentFields.filter(
            (field) =>
                field.visible
        );


    container.innerHTML =
        visibleFields
            .map(
                (field) => {

                    const value =
                        getFieldValue(
                            field,
                            equipment
                        );


                    return createFieldHtml(
                        field,
                        value
                    );

                }
            )
            .join("");

}


async function loadAssets() {

    const tableBody =
        document.getElementById(
            "assets-table-body"
        );


    const equipmentCount =
        document.getElementById(
            "equipment-count"
        );


    if (!tableBody) {
        return;
    }


    tableBody.innerHTML = `
        <tr>

            <td
                colspan="10"
                class="loading-cell"
            >
                Loading equipment...
            </td>

        </tr>
    `;


    try {

        const equipments =
            await apiRequest(
                "/api/equipments"
            );


        if (equipmentCount) {

            equipmentCount.textContent =
                `${equipments.length} ${
                    equipments.length === 1
                        ? "item"
                        : "items"
                }`;

        }


        if (
            equipments.length === 0
        ) {

            tableBody.innerHTML = `
                <tr>

                    <td
                        colspan="9"
                        class="empty-cell"
                    >
                        No equipment available.
                    </td>

                </tr>
            `;

            return;
        }


        tableBody.innerHTML =
            equipments
                .map(
                    (equipment, equipmentRowIndex) => {

                        const criticality =
                            equipment.criticality ||
                            "-";


                        return `
                            <tr>

                                <td>
                                    ${equipmentRowIndex + 1}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        equipment.name ||
                                        "-"
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        equipment.device_type ||
                                        "-"
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        equipment.vendor ||
                                        "-"
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        equipment.model ||
                                        "-"
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        equipment.version ||
                                        "-"
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        equipment.ip_address ||
                                        "-"
                                    )}
                                </td>

                                <td>

                                    <span
                                        class="
                                            criticality-badge
                                            criticality-${String(
                                                criticality
                                            ).toLowerCase()}
                                        "
                                    >
                                        ${escapeHtml(
                                            criticality
                                        )}
                                    </span>

                                </td>

                                <td>
                                    ${escapeHtml(
                                        equipment.environment ||
                                        "-"
                                    )}
                                </td>

                                <td>

                                    <div class="table-actions">

                                        <button
                                            type="button"
                                            class="secondary-button small-button"
                                            onclick="editEquipment(${equipment.id})"
                                        >
                                            Edit
                                        </button>


                                        <button
                                            type="button"
                                            class="danger-button small-button"
                                            onclick="deleteEquipment(${equipment.id})"
                                        >
                                            Delete
                                        </button>

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
                    colspan="9"
                    class="error-cell"
                >

                    Failed to load equipment.

                    <br>

                    ${escapeHtml(
                        error.message
                    )}

                </td>

            </tr>
        `;

    }

}


function openEquipmentForm() {

    editingEquipmentId = null;


    document.getElementById(
        "equipment-form-title"
    ).textContent =
        "Add Equipment";


    renderEquipmentForm();


    document.getElementById(
        "equipment-form-container"
    ).style.display =
        "block";


    document.getElementById(
        "equipment-form-container"
    ).scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


function closeEquipmentForm() {

    document.getElementById(
        "equipment-form-container"
    ).style.display =
        "none";


    editingEquipmentId = null;


    const form =
        document.getElementById(
            "equipment-form"
        );


    if (form) {
        form.reset();
    }

}


async function editEquipment(id) {

    try {

        const equipment =
            await apiRequest(
                `/api/equipments/${id}`
            );


        editingEquipmentId = id;


        document.getElementById(
            "equipment-form-title"
        ).textContent =
            "Edit Equipment";


        renderEquipmentForm(
            equipment
        );


        document.getElementById(
            "equipment-form-container"
        ).style.display =
            "block";


        document.getElementById(
            "equipment-form-container"
        ).scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (error) {

        console.error(error);


        alert(
            `Failed to load equipment.\n\n${error.message}`
        );

    }

}


function collectFormData() {

    const equipmentData = {};

    const customFields = {};


    for (
        const field
        of equipmentFields
    ) {

        if (!field.visible) {
            continue;
        }


        const element =
            document.getElementById(
                `field_${field.field_key}`
            );


        if (!element) {
            continue;
        }


        let value;


        if (
            field.field_type ===
            "multiselect"
        ) {

            value =
                Array.from(
                    element.selectedOptions
                ).map(
                    (option) =>
                        option.value
                );

        } else {

            value =
                element.value.trim();

        }


        if (
            value === ""
            ||
            (
                Array.isArray(value)
                &&
                value.length === 0
            )
        ) {

            value = null;

        }


        if (field.system_field) {

            equipmentData[
                field.field_key
            ] = value;

        } else {

            customFields[
                field.field_key
            ] = value;

        }

    }


    equipmentData.custom_fields =
        customFields;


    return equipmentData;

}


async function saveEquipment(event) {

    event.preventDefault();


    const equipmentData =
        collectFormData();


    try {

        if (
            editingEquipmentId === null
        ) {

            await apiRequest(
                "/api/equipments",
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            equipmentData
                        )
                }
            );

        } else {

            await apiRequest(
                `/api/equipments/${editingEquipmentId}`,
                {
                    method: "PUT",

                    body:
                        JSON.stringify(
                            equipmentData
                        )
                }
            );

        }


        closeEquipmentForm();


        await loadAssets();


    } catch (error) {

        console.error(error);


        alert(
            `Failed to save equipment.\n\n${error.message}`
        );

    }

}


async function deleteEquipment(id) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this equipment?"
        );


    if (!confirmed) {
        return;
    }


    try {

        await apiRequest(
            `/api/equipments/${id}`,
            {
                method: "DELETE"
            }
        );


        await loadAssets();


    } catch (error) {

        console.error(error);


        alert(
            `Failed to delete equipment.\n\n${error.message}`
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
    async () => {

        try {

            await loadEquipmentFields();

            await loadAssets();

        } catch (error) {

            console.error(
                "Failed to initialize assets page:",
                error
            );

        }


        const addButton =
            document.getElementById(
                "add-asset-button"
            );


        const cancelButton =
            document.getElementById(
                "cancel-equipment-button"
            );


        const form =
            document.getElementById(
                "equipment-form"
            );


        if (addButton) {

            addButton.addEventListener(
                "click",
                openEquipmentForm
            );

        }


        if (cancelButton) {

            cancelButton.addEventListener(
                "click",
                closeEquipmentForm
            );

        }


        if (form) {

            form.addEventListener(
                "submit",
                saveEquipment
            );

        }

    }
);