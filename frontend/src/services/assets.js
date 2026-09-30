let editingEquipmentId = null;


async function loadAssets() {

    const tableBody = document.getElementById(
        "assets-table-body"
    );

    const equipmentCount = document.getElementById(
        "equipment-count"
    );


    if (!tableBody) {
        return;
    }


    tableBody.innerHTML = `
        <tr>
            <td colspan="9" class="loading-cell">
                Loading equipment...
            </td>
        </tr>
    `;


    try {

        const equipments = await apiRequest(
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


        if (equipments.length === 0) {

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


        tableBody.innerHTML = equipments
            .map(
                (equipment) => {

                    return `
                        <tr>

                            <td>
                                ${escapeHtml(
                                    equipment.name
                                )}
                            </td>

                            <td>
                                ${escapeHtml(
                                    equipment.device_type || "-"
                                )}
                            </td>

                            <td>
                                ${escapeHtml(
                                    equipment.vendor || "-"
                                )}
                            </td>

                            <td>
                                ${escapeHtml(
                                    equipment.model || "-"
                                )}
                            </td>

                            <td>
                                ${escapeHtml(
                                    equipment.version || "-"
                                )}
                            </td>

                            <td>
                                ${escapeHtml(
                                    equipment.ip_address || "-"
                                )}
                            </td>

                            <td>
                                <span class="
                                    criticality-badge
                                    criticality-${String(
                                        equipment.criticality
                                    ).toLowerCase()}
                                ">
                                    ${escapeHtml(
                                        equipment.criticality
                                    )}
                                </span>
                            </td>

                            <td>
                                ${escapeHtml(
                                    equipment.environment
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
                    ${escapeHtml(error.message)}
                </td>
            </tr>
        `;

    }

}


function openEquipmentForm() {

    const container = document.getElementById(
        "equipment-form-container"
    );

    const title = document.getElementById(
        "equipment-form-title"
    );


    editingEquipmentId = null;


    title.textContent =
        "Add Equipment";


    document
        .getElementById("equipment-form")
        .reset();


    container.style.display =
        "block";


    container.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


function closeEquipmentForm() {

    const container = document.getElementById(
        "equipment-form-container"
    );


    container.style.display =
        "none";


    editingEquipmentId = null;


    document
        .getElementById("equipment-form")
        .reset();

}


async function editEquipment(id) {

    try {

        const equipment = await apiRequest(
            `/api/equipments/${id}`
        );


        editingEquipmentId = id;


        document.getElementById(
            "equipment-form-title"
        ).textContent =
            "Edit Equipment";


        document.getElementById(
            "name"
        ).value =
            equipment.name || "";


        document.getElementById(
            "device_type"
        ).value =
            equipment.device_type || "";


        document.getElementById(
            "vendor"
        ).value =
            equipment.vendor || "";


        document.getElementById(
            "model"
        ).value =
            equipment.model || "";


        document.getElementById(
            "version"
        ).value =
            equipment.version || "";


        document.getElementById(
            "ip_address"
        ).value =
            equipment.ip_address || "";


        document.getElementById(
            "serial_number"
        ).value =
            equipment.serial_number || "";


        document.getElementById(
            "cpe"
        ).value =
            equipment.cpe || "";


        document.getElementById(
            "criticality"
        ).value =
            equipment.criticality || "Medium";


        document.getElementById(
            "environment"
        ).value =
            equipment.environment || "Production";


        document.getElementById(
            "description"
        ).value =
            equipment.description || "";


        const container =
            document.getElementById(
                "equipment-form-container"
            );


        container.style.display =
            "block";


        container.scrollIntoView({
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


async function saveEquipment(event) {

    event.preventDefault();


    const equipmentData = {

        name:
            document.getElementById(
                "name"
            ).value.trim(),

        device_type:
            document.getElementById(
                "device_type"
            ).value.trim() || null,

        vendor:
            document.getElementById(
                "vendor"
            ).value.trim() || null,

        model:
            document.getElementById(
                "model"
            ).value.trim() || null,

        version:
            document.getElementById(
                "version"
            ).value.trim() || null,

        ip_address:
            document.getElementById(
                "ip_address"
            ).value.trim() || null,

        serial_number:
            document.getElementById(
                "serial_number"
            ).value.trim() || null,

        cpe:
            document.getElementById(
                "cpe"
            ).value.trim() || null,

        criticality:
            document.getElementById(
                "criticality"
            ).value,

        environment:
            document.getElementById(
                "environment"
            ).value,

        description:
            document.getElementById(
                "description"
            ).value.trim() || null

    };


    try {

        if (editingEquipmentId === null) {

            await apiRequest(
                "/api/equipments",
                {
                    method: "POST",
                    body: JSON.stringify(
                        equipmentData
                    )
                }
            );

        } else {

            await apiRequest(
                `/api/equipments/${editingEquipmentId}`,
                {
                    method: "PUT",
                    body: JSON.stringify(
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

    const confirmed = confirm(
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
        document.createElement("div");


    element.textContent =
        value;


    return element.innerHTML;

}


document.addEventListener(
    "DOMContentLoaded",
    () => {

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


        loadAssets();

    }
);