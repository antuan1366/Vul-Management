let vulnerabilities = [];
let candidates = [];

function escapeVulnerabilityHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function renderVulnerabilities() {
    const body = document.getElementById("vulnerabilities-table-body");
    const count = document.getElementById("vulnerability-count");
    if (!body) return;

    if (count) count.textContent = vulnerabilities.length + " Vulnerabilities";

    if (!vulnerabilities.length) {
        body.innerHTML = '<tr><td colspan="7" class="empty-cell">No approved vulnerabilities.</td></tr>';
        return;
    }

    body.innerHTML = vulnerabilities.map(function(item, index) {
        return "<tr>" +
            "<td>" + (index + 1) + "</td>" +
            "<td><strong>" + escapeVulnerabilityHtml(item.cve_id) + "</strong></td>" +
            "<td>" + escapeVulnerabilityHtml(item.severity || "-") + "</td>" +
            "<td>" + escapeVulnerabilityHtml(item.cvss_score ?? "-") + "</td>" +
            "<td>" + escapeVulnerabilityHtml(item.affected_product || "-") + "</td>" +
            "<td>" + (item.cisa_kev ? "Yes" : "No") + "</td>" +
            "<td>" + escapeVulnerabilityHtml((item.description || "").slice(0, 160) || "-") + "</td>" +
            "</tr>";
    }).join("");
}

function renderCandidates() {
    const body = document.getElementById("candidate-table-body");
    const count = document.getElementById("candidate-count");
    if (!body) return;

    if (count) count.textContent = candidates.length + " Candidates";

    if (!candidates.length) {
        body.innerHTML = '<tr><td colspan="8" class="empty-cell">No findings waiting for review.</td></tr>';
        return;
    }

    body.innerHTML = candidates.map(function(item, index) {
        return "<tr>" +
            "<td>" + (index + 1) + "</td>" +
            "<td><strong>" + escapeVulnerabilityHtml(item.cve_id) + "</strong></td>" +
            "<td>" + escapeVulnerabilityHtml(item.asset_type + " #" + item.asset_id) + "</td>" +
            "<td>" + escapeVulnerabilityHtml(item.severity || "-") + "</td>" +
            "<td>" + escapeVulnerabilityHtml(item.cvss_score ?? "-") + "</td>" +
            "<td>" + escapeVulnerabilityHtml(item.match_status || "-") + "</td>" +
            "<td>" + escapeVulnerabilityHtml(item.confidence ?? "-") + "%</td>" +
            "<td><div class=\"table-actions\">" +
                "<button class=\"primary-button small-button\" onclick="approveCandidate(" + item.id + ")\">Approve</button>" +
                "<button class=\"danger-button small-button\" onclick="rejectCandidate(" + item.id + ")">Reject</button>" +
            "</div></td>" +
            "</tr>";
    }).join("");
}

async function loadVulnerabilities() {
    try {
        const result = await apiRequest("/api/intelligence/vulnerabilities");
        vulnerabilities = result.items || [];
        renderVulnerabilities();
    } catch (error) {
        document.getElementById("vulnerabilities-table-body").innerHTML =
            '<tr><td colspan="7" class="error-cell">' + escapeVulnerabilityHtml(error.message) + "</td></tr>";
    }
}

async function loadCandidates() {
    try {
        const result = await apiRequest("/api/vulnerability-candidates?status=pending");
        candidates = result.items || [];
        renderCandidates();
    } catch (error) {
        document.getElementById("candidate-table-body").innerHTML =
            '<tr><td colspan="8" class="error-cell">' + escapeVulnerabilityHtml(error.message) + "</td></tr>";
    }
}

async function approveCandidate(id) {
    const notes = prompt("Review notes (optional):", "") ?? "";
    try {
        await apiRequest("/api/vulnerability-candidates/" + id + "/approve", {
            method: "POST",
            body: JSON.stringify({ notes: notes || null })
        });
        await Promise.all([loadCandidates(), loadVulnerabilities()]);
    } catch (error) {
        alert("Approval failed.\n\n" + error.message);
    }
}

async function rejectCandidate(id) {
    const notes = prompt("Reason for rejection:", "") ?? "";
    if (!confirm("Reject this finding?")) return;
    try {
        await apiRequest("/api/vulnerability-candidates/" + id + "/reject", {
            method: "POST",
            body: JSON.stringify({ notes: notes || null })
        });
        await loadCandidates();
    } catch (error) {
        alert("Rejection failed.\n\n" + error.message);
    }
}

async function syncNvd() {
    const button = document.getElementById("sync-nvd-button");
    const days = Math.max(1, Math.min(120, Number(document.getElementById("nvd-days-back")?.value || 5)));
    if (button) { button.disabled = true; button.textContent = "Starting..."; }

    try {
        const result = await apiRequest("/api/intelligence/nvd/sync?days_back=" + days, { method: "POST" });
        window.location.href = "sync-status.html?job=" + result.job_id;
    } catch (error) {
        alert(error.message);
    } finally {
        if (button) { button.disabled = false; button.textContent = "Discover NVD Findings"; }
    }
}

async function syncCisaKev() {
    const button = document.getElementById("sync-kev-button");
    if (button) { button.disabled = true; button.textContent = "Starting..."; }
    try {
        const result = await apiRequest("/api/intelligence/cisa-kev/sync", { method: "POST" });
        window.location.href = "sync-status.html?job=" + result.job_id;
    } catch (error) {
        alert(error.message);
    } finally {
        if (button) { button.disabled = false; button.textContent = "Sync CISA KEV"; }
    }
}

function initializeVulnerabilitiesPage() {
    document.getElementById("sync-nvd-button")?.addEventListener("click", syncNvd);
    document.getElementById("sync-kev-button")?.addEventListener("click", syncCisaKev);
    Promise.all([loadCandidates(), loadVulnerabilities()]);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeVulnerabilitiesPage);
} else {
    initializeVulnerabilitiesPage();
}