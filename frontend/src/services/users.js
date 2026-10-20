let users = [];
let editingUserId = null;

function escapeUserHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function userDateLabel(value) {
    if (!value) return "Never";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Unknown";
    return date.toLocaleString();
}

function renderUsers() {
    const body = document.getElementById("users-table-body");
    const count = document.getElementById("user-count");
    if (!body) return;

    if (count) count.textContent = users.length + " user" + (users.length === 1 ? "" : "s");
    if (!users.length) {
        body.innerHTML = '<tr><td colspan="7" class="empty-cell">No users configured.</td></tr>';
        return;
    }

    body.innerHTML = users.map(function (user, index) {
        const status = user.is_active ? "Active" : "Disabled";
        return [
            "<tr>",
            "<td>" + (index + 1) + "</td>",
            "<td><strong>" + escapeUserHtml(user.display_name) + "</strong></td>",
            "<td>" + escapeUserHtml(user.username) + "</td>",
            "<td>" + (user.role === "admin" ? "Administrator" : "User") + "</td>",
            "<td>" + status + "</td>",
            '<td title="' + escapeUserHtml(user.last_login_at || "") + '">' + escapeUserHtml(userDateLabel(user.last_login_at)) + "</td>",
            '<td><div class="table-actions">',
            '<button type="button" class="secondary-button small-button" data-action="edit" data-id="' + user.id + '">Edit</button>',
            '<button type="button" class="danger-button small-button" data-action="delete" data-id="' + user.id + '">Delete</button>',
            "</div></td>",
            "</tr>"
        ].join("");
    }).join("");
}

async function loadUsers() {
    const body = document.getElementById("users-table-body");
    try {
        users = await apiRequest("/api/users");
        renderUsers();
    } catch (error) {
        if (body) {
            body.innerHTML = '<tr><td colspan="7" class="error-cell">' +
                escapeUserHtml(error.message) + "</td></tr>";
        }
    }
}

function openUserModal(user) {
    editingUserId = user ? user.id : null;
    document.getElementById("user-form-title").textContent = user ? "Edit User" : "Add User";
    document.getElementById("user_username").value = user ? user.username : "";
    document.getElementById("user_username").disabled = Boolean(user);
    document.getElementById("user_display_name").value = user ? user.display_name : "";
    document.getElementById("user_password").value = "";
    document.getElementById("user_password").required = !user;
    document.getElementById("password-required-marker").style.display = user ? "none" : "inline";
    document.getElementById("password-help").textContent = user
        ? "Leave blank to keep the current password; enter 12+ characters to reset it."
        : "At least 12 characters.";
    document.getElementById("user_role").value = user ? user.role : "user";
    document.getElementById("user_is_active").checked = user ? Boolean(user.is_active) : true;
    document.getElementById("user-form-message").textContent = "";
    document.getElementById("user-form-message").classList.remove("is-error");

    const modal = document.getElementById("user-modal");
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
}

function closeUserModal() {
    const modal = document.getElementById("user-modal");
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    editingUserId = null;
}

async function saveUser(event) {
    event.preventDefault();
    const password = document.getElementById("user_password").value;
    const payload = {
        display_name: document.getElementById("user_display_name").value.trim(),
        role: document.getElementById("user_role").value,
        is_active: document.getElementById("user_is_active").checked
    };
    if (!editingUserId) {
        payload.username = document.getElementById("user_username").value.trim();
        payload.password = password;
    } else if (password) {
        payload.password = password;
    }

    const button = document.getElementById("save-user-button");
    button.disabled = true;
    button.textContent = "Saving...";
    try {
        if (editingUserId) {
            await apiRequest("/api/users/" + editingUserId, {
                method: "PATCH",
                body: JSON.stringify(payload)
            });
        } else {
            await apiRequest("/api/users", {
                method: "POST",
                body: JSON.stringify(payload)
            });
        }
        closeUserModal();
        await loadUsers();
    } catch (error) {
        const message = document.getElementById("user-form-message");
        message.textContent = error.message || "The user could not be saved.";
        message.classList.add("is-error");
    } finally {
        button.disabled = false;
        button.textContent = "Save User";
    }
}

async function handleUserAction(event) {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    const userId = Number(button.dataset.id);
    const user = users.find(function (item) { return item.id === userId; });
    if (!user) return;

    if (button.dataset.action === "edit") {
        openUserModal(user);
        return;
    }
    if (button.dataset.action === "delete") {
        if (!confirm('Delete user "' + user.username + '"? This cannot be undone.')) return;
        try {
            await apiRequest("/api/users/" + userId, { method: "DELETE" });
            await loadUsers();
        } catch (error) {
            alert(error.message);
        }
    }
}

function initializeUsersPage() {
    document.getElementById("add-user-button")?.addEventListener("click", function () {
        openUserModal(null);
    });
    document.getElementById("close-user-modal")?.addEventListener("click", closeUserModal);
    document.getElementById("cancel-user-button")?.addEventListener("click", closeUserModal);
    document.getElementById("user-form")?.addEventListener("submit", saveUser);
    document.getElementById("users-table-body")?.addEventListener("click", handleUserAction);
    document.getElementById("user-modal")?.addEventListener("click", function (event) {
        if (event.target.id === "user-modal") closeUserModal();
    });
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" &&
            document.getElementById("user-modal")?.classList.contains("is-open")) {
            closeUserModal();
        }
    });
    loadUsers();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeUsersPage);
} else {
    initializeUsersPage();
}
