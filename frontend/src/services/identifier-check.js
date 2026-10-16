(function () {
    const statusLabels = {
        verified: "Verified",
        pending_verification: "Verify",
        multiple_matches: "Multiple Matches",
        not_found: "Not Found",
        insufficient_data: "Insufficient Data",
        feed_unavailable: "Feed Unavailable",
        error: "Check Failed",
        unverified: "Not Checked"
    };

    function escapeHtml(value) {
        const element = document.createElement("div");
        element.textContent = value ?? "";
        return element.innerHTML;
    }

    function statusLabel(status) {
        return statusLabels[status] || status || "Unknown";
    }

    function statusClass(status) {
        return "identifier-" + String(status || "unverified").replace(/_/g, "-");
    }

    async function loadIdentifierMap(assetType) {
        const items = await apiRequest("/api/security-identifiers?asset_type=" + encodeURIComponent(assetType));
        return Object.fromEntries(items.map(item => [String(item.asset_id), item]));
    }

    function renderIdentifierStatus(identifier, assetType, assetId) {
        if (!identifier) {
            return '<button type="button" class="identifier-status identifier-unverified" onclick="showIdentifierDetails(\'' +
                escapeHtml(assetType) + '\',' + assetId + ')">Not Checked</button>';
        }
        return '<button type="button" class="identifier-status ' + statusClass(identifier.verification_status) +
            '" onclick="showIdentifierDetails(\'' + escapeHtml(assetType) + '\',' + assetId + ')">' +
            escapeHtml(statusLabel(identifier.verification_status)) + "</button>";
    }

    function ensureModal() {
        if (document.getElementById("identifier-check-modal")) return;
        const modal = document.createElement("div");
        modal.id = "identifier-check-modal";
        modal.className = "modal-overlay";
        modal.setAttribute("aria-hidden", "true");
        modal.innerHTML =
            '<div class="modal-dialog identifier-check-dialog" role="dialog" aria-modal="true">' +
            '<div class="modal-header"><div><h2 id="identifier-check-title">Online Identification Check</h2>' +
            '<p id="identifier-check-description" class="section-description"></p></div>' +
            '<button type="button" class="modal-close-button" id="identifier-check-close" aria-label="Close">&times;</button></div>' +
            '<div id="identifier-check-progress"></div><div id="identifier-check-results"></div></div>';
        document.body.appendChild(modal);
        modal.addEventListener("click", event => {
            if (event.target === modal) closeModal();
        });
        document.getElementById("identifier-check-close").addEventListener("click", closeModal);
    }

    function openModal(title, description) {
        ensureModal();
        document.getElementById("identifier-check-title").textContent = title;
        document.getElementById("identifier-check-description").textContent = description || "";
        document.getElementById("identifier-check-progress").innerHTML = "";
        document.getElementById("identifier-check-results").innerHTML = "";
        const modal = document.getElementById("identifier-check-modal");
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
    }

    function closeModal() {
        const modal = document.getElementById("identifier-check-modal");
        if (!modal) return;
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
    }

    async function startOnlineIdentifierCheck(assetType, label) {
        openModal("Online Identification Check", "Checking all " + label.toLowerCase() + ". Results are saved for administrator verification.");
        const progress = document.getElementById("identifier-check-progress");
        const results = document.getElementById("identifier-check-results");
        progress.innerHTML =
            '<div class="identifier-progress"><div class="identifier-progress-bar" id="identifier-progress-bar"></div></div>' +
            '<div id="identifier-progress-text" class="section-description">Starting...</div>';

        try {
            const started = await apiRequest(
                "/api/intelligence/assets/" + encodeURIComponent(assetType) + "/check",
                { method: "POST" }
            );
            let finished = false;
            while (!finished) {
                const job = await apiRequest("/api/sync-jobs/" + started.job_id);
                const bar = document.getElementById("identifier-progress-bar");
                const text = document.getElementById("identifier-progress-text");
                if (bar) bar.style.width = (job.progress || 0) + "%";
                if (text) text.textContent = (job.current_step || "Checking assets...") +
                    " — " + (job.processed || 0) + " / " + (job.total || 0);

                if (job.status === "completed") {
                    finished = true;
                    renderCheckResults(job.result?.results || []);
                } else if (job.status === "failed" || job.status === "cancelled") {
                    finished = true;
                    results.innerHTML = '<div class="error-cell">' +
                        escapeHtml(job.error_message || "Identification check failed.") + "</div>";
                } else {
                    await new Promise(resolve => setTimeout(resolve, 1200));
                }
            }
        } catch (error) {
            results.innerHTML = '<div class="error-cell">' + escapeHtml(error.message) + "</div>";
        }
    }

    function renderCheckResults(items) {
        const progressText = document.getElementById("identifier-progress-text");
        if (progressText) progressText.textContent = "Completed — " + items.length + " assets checked.";
        const results = document.getElementById("identifier-check-results");
        if (!items.length) {
            results.innerHTML = '<div class="empty-cell">No assets exist in this asset category.</div>';
            return;
        }
        results.innerHTML = '<div class="identifier-result-list">' + items.map(item => {
            const identifier = item.cpe || item.purl || "";
            return '<div class="identifier-result-row">' +
                '<div><strong>' + escapeHtml(item.asset_name) + '</strong><div class="section-description">' +
                escapeHtml(identifier || item.reason || "No identifier") + '</div></div>' +
                '<span class="identifier-status ' + statusClass(item.status) + '">' +
                escapeHtml(statusLabel(item.status)) + '</span></div>';
        }).join("") + "</div>";
    }

    async function showIdentifierDetails(assetType, assetId) {
        openModal("Identification Details", "Review the automatically discovered identifier before vulnerability discovery.");
        const results = document.getElementById("identifier-check-results");
        results.innerHTML = '<div class="loading-cell">Loading identification details...</div>';

        try {
            const item = await apiRequest("/api/security-identifiers/" + encodeURIComponent(assetType) + "/" + assetId);
            const candidates = item.candidates || [];
            let candidateHtml = "";
            if (candidates.length) {
                candidateHtml = '<div class="identifier-candidates"><h3>Candidates</h3>' +
                    candidates.map((candidate, index) => {
                        const value = candidate.cpe || "";
                        return '<label class="identifier-candidate">' +
                            '<input type="radio" name="identifier-candidate" value="' + escapeHtml(value) + '"' +
                            (index === 0 ? " checked" : "") + '>' +
                            '<span><strong>' + escapeHtml(value) + '</strong><small>' +
                            escapeHtml(candidate.title || ("Score: " + (candidate.score ?? "-"))) +
                            '</small></span></label>';
                    }).join("") + "</div>";
            }

            const current = item.cpe || item.purl || "None";
            const canVerify = Boolean(item.cpe || item.purl || candidates.length);
            results.innerHTML =
                '<div class="identifier-detail-card">' +
                '<div><strong>Status</strong><span class="identifier-status ' + statusClass(item.verification_status) + '">' +
                escapeHtml(statusLabel(item.verification_status)) + '</span></div>' +
                '<div><strong>Current Identifier</strong><code>' + escapeHtml(current) + '</code></div>' +
                '<div><strong>Source</strong><span>' + escapeHtml(item.source || "—") + '</span></div>' +
                '<div><strong>Confidence</strong><span>' + escapeHtml(item.confidence == null ? "—" : item.confidence + "%") + '</span></div>' +
                '<div><strong>Reason</strong><span>' + escapeHtml(item.reason || "—") + '</span></div>' +
                candidateHtml +
                (canVerify ? '<div class="form-actions"><button type="button" class="primary-button" id="verify-identifier-button">Verify</button></div>' : '') +
                '</div>';

            document.getElementById("verify-identifier-button")?.addEventListener("click", async () => {
                const selected = document.querySelector('input[name="identifier-candidate"]:checked')?.value;
                const payload = item.purl ? { purl: item.purl } : { cpe: selected || item.cpe };
                if (!payload.cpe && !payload.purl) {
                    alert("Select an identifier first.");
                    return;
                }
                try {
                    await apiRequest(
                        "/api/security-identifiers/" + encodeURIComponent(assetType) + "/" + assetId + "/verify",
                        { method: "POST", body: JSON.stringify(payload) }
                    );
                    closeModal();
                    window.location.reload();
                } catch (error) {
                    alert(error.message);
                }
            });
        } catch (error) {
            results.innerHTML = '<div class="error-cell">' + escapeHtml(error.message) + "</div>";
        }
    }

    window.loadIdentifierMap = loadIdentifierMap;
    window.renderIdentifierStatus = renderIdentifierStatus;
    window.startOnlineIdentifierCheck = startOnlineIdentifierCheck;
    window.showIdentifierDetails = showIdentifierDetails;

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("[data-online-identifier-check]").forEach(button => {
            button.addEventListener("click", () => startOnlineIdentifierCheck(
                button.dataset.assetType,
                button.dataset.assetLabel || "assets"
            ));
        });
    });
})();
