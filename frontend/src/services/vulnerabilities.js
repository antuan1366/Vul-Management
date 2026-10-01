
let vulnerabilities = [];

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

    if (!body) {
        return;
    }

    if (count) {
        count.textContent =
            vulnerabilities.length +
            " Vulnerabilit" +
            (vulnerabilities.length === 1 ? "y" : "ies");
    }

    if (!vulnerabilities.length) {
        body.innerHTML =
            '<tr><td colspan="7" class="empty-cell">No vulnerabilities synchronized yet.</td></tr>';
        return;
    }

    body.innerHTML = vulnerabilities.map(function (item, index) {
        return [
            "<tr>",
            "<td>" + (index + 1) + "</td>",
            "<td><strong>" + escapeVulnerabilityHtml(item.cve_id) + "</strong></td>",
            "<td>" + escapeVulnerabilityHtml(item.severity || "-") + "</td>",
            "<td>" + escapeVulnerabilityHtml(item.cvss_score ?? "-") + "</td>",
            "<td>" + escapeVulnerabilityHtml(item.affected_product || "-") + "</td>",
            "<td>" + (item.cisa_kev ? "Yes" : "No") + "</td>",
            "<td>" + escapeVulnerabilityHtml(
                (item.description || "").slice(0, 160) || "-"
            ) + "</td>",
            "</tr>"
        ].join("");
    }).join("");
}

async function loadVulnerabilities() {
    const body = document.getElementById("vulnerabilities-table-body");

    if (body) {
        body.innerHTML =
            '<tr><td colspan="7" class="loading-cell">Loading vulnerabilities...</td></tr>';
    }

    try {
        const result = await apiRequest("/api/intelligence/vulnerabilities");
        vulnerabilities = result.items || [];
        renderVulnerabilities();
    } catch (error) {
        if (body) {
            body.innerHTML =
                '<tr><td colspan="7" class="error-cell">' +
                escapeVulnerabilityHtml(error.message) +
                "</td></tr>";
        }
    }
}

async function syncNvd() {
    const button = document.getElementById("sync-nvd-button");
    if (button) {
        button.disabled = true;
        button.textContent = "Syncing...";
    }
    try {
        const result = await apiRequest("/api/intelligence/nvd/sync?days_back=7", { method: "POST" });
        alert("NVD synchronization completed. Created " + result.created + " and updated " + result.updated + " vulnerabilities.");
        await loadVulnerabilities();
    } catch (error) {
        alert(error.message);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = "Sync NVD";
        }
    }
}

async function syncCisaKev() {
    const button = document.getElementById("sync-kev-button");
    if (button) {
        button.disabled = true;
        button.textContent = "Syncing...";
    }

    try {
        const result = await apiRequest(
            "/api/intelligence/cisa-kev/sync",
            { method: "POST" }
        );

        alert(
            "CISA KEV sync completed. Updated " +
            result.updated_vulnerabilities +
            " vulnerabilities."
        );

        await loadVulnerabilities();
    } catch (error) {
        alert(error.message);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = "Sync CISA KEV";
        }
    }
}

function initializeVulnerabilitiesPage() {
    document.getElementById("sync-nvd-button")?.addEventListener("click", syncNvd);
    document.getElementById("sync-kev-button")?.addEventListener("click", syncCisaKev);

    loadVulnerabilities();
}

if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initializeVulnerabilitiesPage
    );
} else {
    initializeVulnerabilitiesPage();
}
