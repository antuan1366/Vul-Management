let scanPollTimer = null;

function scanEscape(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function scanDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function scanStatusClass(status) {
    return "status-badge status-" + String(status || "pending").replace(/[^a-z_]/g, "");
}

function resultText(job) {
    if (job.error_message) return job.error_message;
    if (job.result) {
        if (job.result.message) return job.result.message;
        if (job.result.status) return job.result.status;
        return JSON.stringify(job.result);
    }
    return job.current_step || "-";
}

function renderScanResults(jobs) {
    const body = document.getElementById("scan-results-body");
    if (!body) return;

    document.getElementById("scan-count").textContent = jobs.length + " Scans";

    if (!jobs.length) {
        body.innerHTML = '<tr><td colspan="8" class="empty-cell">No vulnerability scans have been executed yet.</td></tr>';
        return;
    }

    body.innerHTML = jobs.map((job, index) =>
        "<tr>" +
        "<td>" + (index + 1) + "</td>" +
        "<td>#" + job.id + "</td>" +
        "<td>" + scanEscape(scanDate(job.started_at || job.created_at)) + "</td>" +
        "<td>" + scanEscape(scanDate(job.finished_at)) + "</td>" +
        "<td><span class=\"" + scanStatusClass(job.status) + "\">" + scanEscape(job.status) + "</span></td>" +
        "<td>" + scanEscape(job.progress ?? 0) + "%</td>" +
        "<td>" + scanEscape(job.current_step || "-") + "</td>" +
        "<td>" + scanEscape(resultText(job)) + "</td>" +
        "</tr>"
    ).join("");
}

async function loadScanJobs() {
    const data = await apiRequest("/api/sync-jobs?job_type=nvd");
    renderScanResults(data.items || []);
}

async function loadSchedule() {
    const frequency = document.getElementById("scan-frequency");
    if (!frequency) return;

    const schedule = await apiRequest("/api/vulnerability-scan/status");

    if (schedule.enabled && schedule.frequency) {
        frequency.value = schedule.frequency;
    } else {
        frequency.value = "now";
    }
}

function currentTimeHHMM() {
    const now = new Date();
    return String(now.getHours()).padStart(2, "0") + ":" +
        String(now.getMinutes()).padStart(2, "0");
}

async function startSelectedScan() {
    const frequency = document.getElementById("scan-frequency");
    const button = document.getElementById("start-scan-button");
    const message = document.getElementById("schedule-message");
    const selectedFrequency = frequency ? frequency.value : "now";

    button.disabled = true;
    button.textContent = "Starting...";
    message.textContent = "";

    try {
        if (selectedFrequency === "now") {
            await apiRequest("/api/vulnerability-scan/schedule", {
                method: "PUT",
                body: JSON.stringify({
                    enabled: false,
                    frequency: "daily",
                    scan_time: "02:00"
                })
            });

            const result = await apiRequest("/api/vulnerability-scan/run", {
                method: "POST"
            });

            message.textContent = "Scan #" + result.job_id + " started.";
        } else {
            const schedule = await apiRequest("/api/vulnerability-scan/schedule", {
                method: "PUT",
                body: JSON.stringify({
                    enabled: true,
                    frequency: selectedFrequency,
                    scan_time: currentTimeHHMM()
                })
            });

            message.textContent = "Scan schedule set to " +
                frequency.options[frequency.selectedIndex].text +
                ". Next scan: " + scanDate(schedule.next_scan_at) + ".";
        }

        await Promise.all([loadScanJobs(), loadSchedule()]);
    } catch (error) {
        message.textContent = error.message;
        alert("Could not start vulnerability scan.\n\n" + error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Start";
    }
}

async function refreshScanPage() {
    try {
        await Promise.all([loadScanJobs(), loadSchedule()]);
    } catch (error) {
        document.getElementById("schedule-message").textContent = error.message;
    }
}

function initializeScanPage() {
    document.getElementById("start-scan-button")?.addEventListener("click", startSelectedScan);
    refreshScanPage();
    scanPollTimer = setInterval(refreshScanPage, 3000);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeScanPage);
} else {
    initializeScanPage();
}