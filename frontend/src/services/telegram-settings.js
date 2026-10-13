(() => {
    const $ = (id) => document.getElementById(id);
    let challengeId = null;

    function showMessage(message, kind = "info") {
        const el = $("telegram-message");
        el.textContent = message || "";
        el.className = "telegram-message visible " + kind;
    }

    function setBusy(button, busy, label) {
        if (!button.dataset.originalLabel) button.dataset.originalLabel = button.textContent;
        button.disabled = busy;
        button.textContent = busy ? label : button.dataset.originalLabel;
    }

    function setStatus(state, title, detail) {
        $("telegram-status").dataset.state = state;
        $("telegram-status-title").textContent = title;
        $("telegram-status-detail").textContent = detail || "";
    }

    async function refreshStatus() {
        setStatus("unknown", "Checking Telegram status…", "Please wait.");
        try {
            const status = await apiRequest("/api/administration/telegram/status");
            if (!$("telegram-api-id").value && status.api_id) {
                $("telegram-api-id").value = status.api_id;
            }
            if (status.authorized) {
                setStatus("connected", "Connected", "Telegram account session is authorized and ready for scans.");
            } else if (status.configured) {
                setStatus("pending", "Configured, not connected", "Credentials are saved. Request a verification code to authorize this Telegram session.");
            } else {
                setStatus("unknown", "Not configured", "Enter your Telegram API ID, API Hash, and phone number to begin.");
            }
        } catch (error) {
            setStatus("error", "Could not read status", error.message || String(error));
        }
    }

    $("telegram-credentials-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = $("telegram-send-code");
        setBusy(button, true, "Requesting code…");
        showMessage("", "info");
        try {
            const result = await apiRequest("/api/administration/telegram/send-code", {
                method: "POST",
                body: JSON.stringify({
                    api_id: $("telegram-api-id").value.trim() || null,
                    api_hash: $("telegram-api-hash").value || null,
                    phone_number: $("telegram-phone").value.trim()
                })
            });
            challengeId = result.challenge_id;
            $("telegram-verification-form").hidden = false;
            $("telegram-verification-code").value = "";
            $("telegram-2fa-password").value = "";
            $("telegram-2fa-field").hidden = true;
            $("telegram-code-instructions").textContent = "Enter the verification code sent by Telegram to " + result.phone_number + ". The code session expires in about 10 minutes.";
            $("telegram-verification-code").focus();
            $("telegram-api-hash").value = "";
            setStatus("pending", "Verification required", "A verification code was requested. Complete verification below.");
            showMessage(result.message || "Verification code requested.", "success");
        } catch (error) {
            showMessage(error.message || String(error), "error");
        } finally {
            setBusy(button, false, "Requesting code…");
        }
    });

    $("telegram-verification-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!challengeId) {
            showMessage("No active verification session. Request a new verification code.", "error");
            return;
        }
        const button = $("telegram-verify-code");
        setBusy(button, true, "Verifying…");
        try {
            const result = await apiRequest("/api/administration/telegram/verify-code", {
                method: "POST",
                body: JSON.stringify({
                    challenge_id: challengeId,
                    code: $("telegram-verification-code").value.trim(),
                    password: $("telegram-2fa-password").value || null
                })
            });
            if (result.requires_2fa) {
                $("telegram-2fa-field").hidden = false;
                $("telegram-2fa-password").required = true;
                $("telegram-2fa-password").focus();
                showMessage(result.message, "info");
                return;
            }
            if (result.authorized) {
                challengeId = null;
                $("telegram-verification-form").hidden = true;
                $("telegram-2fa-password").value = "";
                $("telegram-2fa-password").required = false;
                $("telegram-credentials-form").reset();
                showMessage(result.message, "success");
                await refreshStatus();
            } else {
                showMessage(result.message || "Telegram did not authorize the session.", "error");
            }
        } catch (error) {
            showMessage(error.message || String(error), "error");
        } finally {
            setBusy(button, false, "Verifying…");
        }
    });

    $("telegram-cancel-verification").addEventListener("click", async () => {
        const currentChallenge = challengeId;
        challengeId = null;
        if (currentChallenge) {
            try {
                await apiRequest("/api/administration/telegram/verification/" + encodeURIComponent(currentChallenge), { method: "DELETE" });
            } catch (error) {
                showMessage(error.message || String(error), "error");
            }
        }
        $("telegram-verification-form").hidden = true;
        $("telegram-2fa-field").hidden = true;
        $("telegram-2fa-password").required = false;
        $("telegram-verification-form").reset();
        showMessage("Verification cancelled. You can request a new code when ready.", "info");
    });

    $("telegram-refresh-status").addEventListener("click", refreshStatus);
    refreshStatus();
})();
