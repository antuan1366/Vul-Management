let findings = [];

function escapeVulnerabilityHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
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
    if (!body) return;

    if (count) count.textContent = findings.length + " Findings";

    if (!findings.length) {
        body.innerHTML = '<tr><td colspan="9" class="empty-cell">No vulnerabilities have been discovered yet.</td></tr>';
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
            candidateFindings.filter(item => item.status === "approved").map(item => item.cve_id)
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
            '<tr><td colspan="9" class="error-cell">' + escapeVulnerabilityHtml(error.message) + "</td></tr>";
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

function initializeVulnerabilitiesPage() {
    loadFindings();
    setInterval(loadFindings, 10000);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeVulnerabilitiesPage);
} else {
    initializeVulnerabilitiesPage();
}