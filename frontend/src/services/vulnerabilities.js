let findings = [];
let scanPollTimer = null;

function escapeVulnerabilityHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDate(value) {
    if (!value) return "Never";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString();
}

function statusClass(status) {
    return {
        pending: "status-pending",
        approved: "status-approved",
        rejected: "status-rejected",
    }[status] || "status-pending";
}

function applicabilityClass(status) {
    if (status === "confirmed_affected") return "status-affected";
    if (status === "not_affected") return "status-not-affected";
    return "status-potential";
}

function humanStatus(status) {
    return {
        pending: "Pending Review",
        approved: "Approved",
        rejected: "Rejected",
    }[status] || status || "-";
}

function humanApplicability(status) {
    return String(status || "-").replaceAll("_", " ");
}

function renderFindings() {
    const body = document.getElementById("findings-table-body");
    const count = document.getElementById("finding-count");
    const pendingCount = document.getElementById("pending-scan-count");
    if (!body) return;

    const pending = findings.filter(item => item.status === "pending").length;
    if (count) count.textContent = findings.length + " Findings";
    if (pendingCount) pendingCount.textContent = pending;

    if (!findings.length) {
        body.innerHTML = '<tr><td colspan="9" class="empty-cell">No vulnerability findings have been discovered yet.</td></tr>';
        return;
    }

    body.innerHTML = findings.map(function(item, index) {
        const actions = item.status === "pending"
            ? "<div class=\"table-actions\">" +
              "<button class=\"primary-button small-button\" onclick=\"approveCandidate(" + item.id + ")\">Approve</button>" +
              "<button class=\"danger-button small-button\" onclick=\"rejectCandidate(" + item.id + ")\">Reject</button>" +
              "</div>"
            : "<span class=\"section-description\">No action</span>";

        return "<tr>" +
            "<td>" + (index + 1) + "</td>" +
            "<td><strong>" + escapeVulnerabilityHtml(item.cve_id) + "</strong></td>" +
            "<td>" + escapeVulnerabilityHtml(item.asset || "-") + "</td>" +
            "<td>" + escapeVulnerabilityHtml(item.severity || "-") + "</td>" +
            "<td>" + escapeVulnerabilityHtml(item.cvss_score ?? "-") + "</td>" +
            "<td><span class=\"status-badge " + applicabilityClass(item.match_status) + "\">" +
                escapeVulnerabilityHtml(humanApplicability(item.match_status)) +
            "</span></td>" +
            "<td><span class=\"status-badge " + statusClass(item.status) + "\">" +
                escapeVulnerabilityHtml(humanStatus(item.status)) +
            "</span></td>" +
            "<td>" + (item.cisa_kev ? "Yes" : "No") + "</td>" +
            "<td>" + actions + "</td>" +
            "</tr>";
    }).join("");
}

async function loadFindings() {
    try {
        const [candidateResult, vulnerabilityResult] = await Promise.all([
            apiRequest("/api/vulnerability-candidates?status=all"),
            apiRequest("/api/intelligence/vulnerabilities")
        ]);

        const candidateFindings = (candidateResult.items || []).map(item => ({
            id: item.id,
            cve_id: item.cve_id,
            asset: item.asset_type + " #" + item.asset_id,
            severity: item.severity,
            cvss_score: item.cvss_score,
            match_status: item.match_status,
            status: item.review_status || "pending",
            cisa_kev: false,
            source: item.source,
            created_at: item.created_at
        }));

        const approvedCves = new Set(
            candidateFindings
                .filter(item => item.status === "approved")
                .map(item => item.cve_id)
        );

        const approvedFindings = (vulnerabilityResult.items || [])
            .filter(item => !approvedCves.has(item.cve_id))
            .map(item => ({
                id: "v-" + item.id,
                cve_id: item.cve_id,
                asset: "Approved vulnerability",
                severity: item.severity,
                cvss_score: item.cvss_score,
                match_status: "confirmed_affected",
                status: "approved",
                cisa_kev: Boolean(item.cisa_kev),
                source: item.source,
                created_at: item.created_at
            }));

        findings = candidateFindings.concat(approvedFindings).sort(function(a, b) {
            const order = { pending: 0, approved: 1, rejected: 2 };
            return (order[a.status] ?? 9) - (order[b.status] ?? 9);
        });

        renderFindings();
    } catch (error) {
        document.getElementById("findings-table-body").innerHTML =
            '<tr><td colspan="9" class="error-cell">' +
            escapeVulnerabilityHtml(error.message) +
            "</td></tr>";
    }
}

async function loadScanStatus() {
    try {
        const status = await apiRequest("/api/vulnerability-scan/status");

        document.getElementById("last-scan").textContent = formatDate(status.last_scan_at);
        document.getElementById("next-scan").textContent =
            status.enabled ? formatDate(status.next_scan_at) : "Not scheduled";
        document.getElementById("scan-status").textContent =
            status.last_status || "Idle";
        document.getElementById("scan-time").value = status.scan_time || "02:00";
        document.getElementById("scan-enabled").checked = Boolean(status.enabled);
        if (status.enabled) {
            document.getElementById("scan-schedule-controls")?.classList.add("open");
        }

        if (status.last_error) {
            document.getElementById("scan-message").textContent = status.last_error;
        } else if (status.last_job_id) {
            document.getElementById("scan-message").textContent =
                "Last scan job #" + status.last_job_id + ".";
        } else {
            document.getElementById("scan-message").textContent =
                "No vulnerability discovery scan has run yet.";
        }
    } catch (error) {
        document.getElementById("scan-message").textContent = error.message;
    }
}

function toggleScanMenu() {
    document.getElementById("scan-menu-panel")?.classList.toggle("open");
}

function openScheduleControls() {
    document.getElementById("scan-menu-panel")?.classList.remove("open");
    document.getElementById("scan-schedule-controls")?.classList.add("open");
}

function closeScanMenuOnOutsideClick(event) {
    const menu = document.querySelector(".scan-menu");
    if (menu && !menu.contains(event.target)) {
        document.getElementById("scan-menu-panel")?.classList.remove("open");
    }
}

async function saveSchedule() {
    const button = document.getElementById("save-schedule-button");
    const enabled = document.getElementById("scan-enabled").checked;
    const scanTime = document.getElementById("scan-time").value || "02:00";

    if (button) {
        button.disabled = true;
        button.textContent = "Saving...";
    }

    try {
        await apiRequest("/api/vulnerability-scan/schedule", {
            method: "PUT",
            body: JSON.stringify({
                enabled: enabled,
                scan_time: scanTime
            })
        });
        await loadScanStatus();
        document.getElementById("scan-message").textContent =
            enabled
                ? "Daily vulnerability scan schedule saved."
                : "Daily vulnerability scan disabled.";
    } catch (error) {
        alert("Could not save the scan schedule.\n\n" + error.message);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = "Save Schedule";
        }
    }
}

async function runScan() {
    const button = document.getElementById("run-scan-button");
    if (button) {
        button.disabled = true;
        button.textContent = "Starting...";
    }

    try {
        await apiRequest("/api/vulnerability-scan/run", { method: "POST" });
        document.getElementById("scan-message").textContent =
            "Vulnerability scan started. The scan is using the current asset inventory. If no assets are defined, the scan will finish with a No Assets status.";
        await loadScanStatus();
        await loadFindings();
    } catch (error) {
        alert("Could not start vulnerability scan.\n\n" + error.message);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = "Scan Now";
        }
    }
}

async function syncCisaKev() {
    const button = document.getElementById("sync-kev-button");
    if (button) {
        button.disabled = true;
        button.textContent = "Updating...";
    }

    try {
        const result = await apiRequest("/api/intelligence/cisa-kev/sync", { method: "POST" });
        document.getElementById("scan-message").textContent =
            "CISA KEV update started as job #" + result.job_id + ".";
        await loadFindings();
    } catch (error) {
        alert("CISA KEV update failed.\n\n" + error.message);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = "Update CISA KEV";
        }
    }
}

async function approveCandidate(id) {
    const notes = prompt("Review notes (optional):", "") ?? "";
    try {
        await apiRequest("/api/vulnerability-candidates/" + id + "/approve", {
            method: "POST",
            body: JSON.stringify({ notes: notes || null })
        });
        await loadFindings();
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
        await loadFindings();
    } catch (error) {
        alert("Rejection failed.\n\n" + error.message);
    }
}

async function refreshVulnerabilityPage() {
    await Promise.all([loadScanStatus(), loadFindings()]);
}

function initializeVulnerabilitiesPage() {
    document.getElementById("scan-menu-button")?.addEventListener("click", toggleScanMenu);
    document.getElementById("one-time-scan-button")?.addEventListener("click", runScan);
    document.getElementById("scheduled-scan-button")?.addEventListener("click", openScheduleControls);
    document.getElementById("save-schedule-button")?.addEventListener("click", saveSchedule);
    document.getElementById("sync-kev-button")?.addEventListener("click", syncCisaKev);
    document.addEventListener("click", closeScanMenuOnOutsideClick);

    refreshVulnerabilityPage();

    scanPollTimer = setInterval(function() {
        refreshVulnerabilityPage();
    }, 5000);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeVulnerabilitiesPage);
} else {
    initializeVulnerabilitiesPage();
}
