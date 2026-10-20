(function () {
    function safeNext(target) {
        if (typeof target !== "string" || !target.startsWith("/src/pages/")) {
            return "/src/pages/dashboard.html";
        }
        if (target.includes("..") || target.startsWith("//") || target.includes("://")) {
            return "/src/pages/dashboard.html";
        }
        if (!target.split("?")[0].endsWith(".html")) {
            return "/src/pages/dashboard.html";
        }
        return target;
    }

    function showMessage(message, isError) {
        const element = document.getElementById("auth-message");
        if (!element) return;
        element.textContent = message || "";
        element.classList.toggle("is-error", Boolean(isError));
        element.classList.toggle("is-success", Boolean(message) && !isError);
    }

    async function redirectIfSetupIsNotValid(page) {
        try {
            const result = await apiRequest("/api/auth/status");
            if (result.setup_required && page !== "setup") {
                window.location.replace("/src/pages/setup.html");
                return true;
            }
            if (!result.setup_required && page === "setup") {
                window.location.replace("/src/pages/login.html");
                return true;
            }
        } catch (error) {
            // The form reports the actionable error when submitted.
        }
        return false;
    }

    async function initializeLogin() {
        const form = document.getElementById("login-form");
        if (!form) return;
        if (await redirectIfSetupIsNotValid("login")) return;

        const params = new URLSearchParams(window.location.search);
        const next = safeNext(params.get("next"));

        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            const button = document.getElementById("login-button");
            button.disabled = true;
            button.textContent = "Signing in...";
            showMessage("");

            try {
                const result = await apiRequest("/api/auth/login", {
                    method: "POST",
                    body: JSON.stringify({
                        username: document.getElementById("username").value.trim(),
                        password: document.getElementById("password").value,
                        next: next
                    })
                });
                window.location.replace(safeNext(result.redirect_to));
            } catch (error) {
                showMessage(error.message || "Sign-in failed.", true);
                button.disabled = false;
                button.textContent = "Sign in";
            }
        });
    }

    async function initializeSetup() {
        const form = document.getElementById("setup-form");
        if (!form) return;
        if (await redirectIfSetupIsNotValid("setup")) return;

        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            const password = document.getElementById("password").value;
            if (password !== document.getElementById("confirm_password").value) {
                showMessage("The passwords do not match.", true);
                return;
            }

            const button = document.getElementById("setup-button");
            button.disabled = true;
            button.textContent = "Creating account...";
            showMessage("");

            try {
                const result = await apiRequest("/api/auth/setup", {
                    method: "POST",
                    body: JSON.stringify({
                        username: document.getElementById("username").value.trim(),
                        display_name: document.getElementById("display_name").value.trim(),
                        password: password
                    })
                });
                window.location.replace(safeNext(result.redirect_to));
            } catch (error) {
                showMessage(error.message || "Initial setup failed.", true);
                button.disabled = false;
                button.textContent = "Create administrator";
            }
        });
    }



    async function initializeChangePassword() {
        const form = document.getElementById("change-password-form");
        if (!form) return;

        try {
            const user = await apiRequest("/api/auth/me");
            if (!user.must_change_password) {
                window.location.replace("/src/pages/dashboard.html");
                return;
            }
        } catch (error) {
            window.location.replace("/src/pages/login.html");
            return;
        }

        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            const currentPassword = document.getElementById("current_password").value;
            const newPassword = document.getElementById("new_password").value;
            if (newPassword !== document.getElementById("confirm_password").value) {
                showMessage("The new passwords do not match.", true);
                return;
            }

            const button = document.getElementById("change-password-button");
            button.disabled = true;
            button.textContent = "Updating password...";
            showMessage("");

            try {
                const result = await apiRequest("/api/auth/change-password", {
                    method: "POST",
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                });
                showMessage("Password updated successfully.", false);
                window.location.replace(safeNext(result.redirect_to));
            } catch (error) {
                showMessage(error.message || "The password could not be changed.", true);
                button.disabled = false;
                button.textContent = "Update password";
            }
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        initializeLogin();
        initializeSetup();
        initializeChangePassword();
    });
})();
