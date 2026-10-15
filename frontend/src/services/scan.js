(() => {
    const $ = (id) => document.getElementById(id);
    let pollTimer = null;
    let activeRunId = null;

    function esc(value) {
        return String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
    }
    function date(value) {
        if (!value) return "—";
        const parsed = new Date(value);
        return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString();
    }
    function pretty(value) {
        return String(value || "unknown").replaceAll("_", " ").replace(/\b\w/g, ch => ch.toUpperCase());
    }
    async function req(url, options) { return apiRequest(url, options); }

    function syncScheduleControls() {
        const enabled = $("scan-schedule-enabled").checked;
        $("scan-schedule-frequency").disabled = !enabled;
        $("scan-schedule-time").disabled = !enabled;
        $("scan-schedule-day").disabled = !enabled || $("scan-schedule-frequency").value !== "weekly";
        $("save-schedule-button").disabled = false;
    }

    async function loadSchedule() {
        const schedule = await req("/api/threat-intelligence/schedule");
        $("scan-schedule-enabled").checked = Boolean(schedule.enabled);
        $("scan-schedule-frequency").value = schedule.frequency || "daily";
        $("scan-schedule-time").value = schedule.scan_time || "02:00";
        $("scan-schedule-day").value = String(schedule.day_of_week ?? 0);
        $("scan-schedule-status").textContent = schedule.enabled
            ? pretty(schedule.frequency) + " at " + (schedule.scan_time || "02:00")
            : "Disabled";
        syncScheduleControls();
    }

    function renderRuns(items) {
        const body = $("scan-log-body");
        $("scan-log-count").textContent = items.length + " Runs";
        if (!items.length) {
            body.innerHTML = '<tr><td colspan="9">No scans have run yet. Use Scan Now to start the first scan.</td></tr>';
            return;
        }
        body.innerHTML = items.map((run, i) => {
            const progress = run.channels_total ? Math.round((run.channels_processed / run.channels_total) * 100) : 0;
            const log = run.error_message || (run.status === "running" || run.status === "pending" ? "Scan in progress…" : "Completed without reported errors");
            return '<tr><td>'+(i+1)+'</td><td>'+esc(run.mode === "from_date" ? "From date" : "New messages")+'</td><td>'+esc(date(run.started_at || run.date))+'</td><td>'+esc(date(run.finished_at))+'</td><td><span class="scan-log-status">'+esc(pretty(run.status))+'</span></td><td>'+esc(run.channels_processed)+' / '+esc(run.channels_total)+'</td><td>'+esc(run.messages_processed)+'</td><td>'+esc(run.cve_occurrences)+'</td><td title="'+esc(log)+'">'+esc(log.length > 150 ? log.slice(0,147)+"…" : log)+'</td></tr>';
        }).join("");
    }

    function renderProgress(run) {
        const wrap = $("scan-progress-wrap");
        if (!run || !["pending","running"].includes(run.status)) {
            wrap.hidden = true;
            if (run) {
                $("scan-last-run").textContent = date(run.finished_at || run.date);
                $("scan-last-status").textContent = pretty(run.status);
                $("scan-last-findings").textContent = String(run.cve_occurrences ?? 0);
            }
            return;
        }
        wrap.hidden = false;
        const total = Number(run.channels_total || 0);
        const done = Number(run.channels_processed || 0);
        const pct = total > 0 ? Math.min(100, Math.round(done / total * 100)) : 0;
        $("scan-progress-label").textContent = run.status === "pending" ? "Scan is queued…" : "Scan is running…";
        $("scan-progress-value").textContent = total > 0 ? pct + "%" : "Starting";
        $("scan-progress-detail").textContent = "Channels processed: " + done + " of " + total + " · Messages: " + (run.messages_processed || 0) + " · CVE occurrences: " + (run.cve_occurrences || 0);
        const bar = $("scan-progress-bar");
        bar.classList.toggle("indeterminate", total === 0);
        if (total > 0) bar.style.width = pct + "%";
        wrap.querySelector('[role="progressbar"]').setAttribute("aria-valuenow", String(pct));
        $("scan-last-run").textContent = date(run.started_at || run.date);
        $("scan-last-status").textContent = pretty(run.status);
        $("scan-last-findings").textContent = String(run.cve_occurrences || 0);
    }

    async function loadRuns() {
        const data = await req("/api/threat-intelligence/scan-runs?limit=100");
        const items = data.items || [];
        renderRuns(items);
        const current = activeRunId ? items.find(x => x.id === activeRunId) : items.find(x => ["pending","running"].includes(x.status));
        if (current) renderProgress(current);
        else if (items.length) renderProgress(items[0]);
        else {
            $("scan-last-run").textContent = "—";
            $("scan-last-status").textContent = "—";
            $("scan-last-findings").textContent = "—";
            $("scan-progress-wrap").hidden = true;
        }
        if (activeRunId) {
            const active = items.find(x => x.id === activeRunId);
            if (active && !["pending","running"].includes(active.status)) {
                activeRunId = null;
                $("scan-progress-label").textContent = "Scan finished";
                $("scan-progress-value").textContent = pretty(active.status);
                $("scan-progress-wrap").hidden = false;
                $("scan-progress-bar").classList.remove("indeterminate");
                $("scan-progress-bar").style.width = "100%";
                $("scan-progress-detail").textContent = (active.error_message || "Scan execution finished.") + " · " + (active.cve_occurrences || 0) + " CVE occurrences";
            }
        }
    }

    async function refresh() {
        const results = await Promise.allSettled([loadSchedule(), loadRuns()]);
        const failed = results.find(x => x.status === "rejected");
        if (failed) $("scan-schedule-message").textContent = failed.reason?.message || String(failed.reason);
    }

    async function startScan(mode) {
        const button = mode === "from_date" ? $("scan-from-date-button") : $("scan-now-button");
        const message = $("scan-schedule-message");
        let start_date;
        if (mode === "from_date") {
            const value = window.prompt("Enter start date/time (YYYY-MM-DDTHH:mm), for example 2026-01-01T00:00");
            if (!value) return;
            if (Number.isNaN(new Date(value).getTime())) {
                window.alert("The date/time format is invalid.");
                return;
            }
            start_date = new Date(value).toISOString();
        }
        button.disabled = true;
        const oldText = button.textContent;
        button.textContent = "Starting…";
        message.textContent = "Starting scan…";
        $("scan-progress-wrap").hidden = false;
        $("scan-progress-label").textContent = "Scan is starting…";
        $("scan-progress-value").textContent = "Starting";
        $("scan-progress-bar").classList.add("indeterminate");
        $("scan-progress-bar").style.width = "35%";
        try {
            const result = await req("/api/threat-intelligence/scan", {
                method: "POST",
                body: JSON.stringify({mode, ...(start_date ? {start_date} : {})})
            });
            activeRunId = result.scan_run_id;
            message.textContent = "Scan #" + result.scan_run_id + " started. Progress and logs are shown below.";
            await loadRuns();
        } catch (error) {
            message.textContent = error.message || String(error);
            $("scan-progress-label").textContent = "Could not start scan";
            $("scan-progress-value").textContent = "Failed";
            $("scan-progress-detail").textContent = message.textContent;
            window.alert("Could not start Telegram scan.\n\n" + message.textContent);
        } finally {
            button.disabled = false;
            button.textContent = oldText;
        }
    }

    async function saveSchedule(event) {
        event.preventDefault();
        const button = $("save-schedule-button");
        button.disabled = true;
        $("scan-schedule-message").textContent = "Saving schedule…";
        try {
            const saved = await req("/api/threat-intelligence/schedule", {
                method: "PUT",
                body: JSON.stringify({
                    enabled: $("scan-schedule-enabled").checked,
                    frequency: $("scan-schedule-frequency").value,
                    scan_time: $("scan-schedule-time").value,
                    day_of_week: Number($("scan-schedule-day").value)
                })
            });
            $("scan-schedule-message").textContent = saved.enabled
                ? "Schedule saved: " + pretty(saved.frequency) + " at " + saved.scan_time + "."
                : "Automatic scan schedule disabled.";
            await loadSchedule();
        } catch (error) {
            $("scan-schedule-message").textContent = error.message || String(error);
        } finally {
            button.disabled = false;
            syncScheduleControls();
        }
    }

    function init() {
        $("scan-schedule-enabled").addEventListener("change", syncScheduleControls);
        $("scan-schedule-frequency").addEventListener("change", syncScheduleControls);
        $("scan-schedule-form").addEventListener("submit", saveSchedule);
        $("scan-now-button").addEventListener("click", () => startScan("new"));
        $("scan-from-date-button").addEventListener("click", () => startScan("from_date"));
        refresh();
        pollTimer = window.setInterval(() => loadRuns().catch(error => {
            $("scan-schedule-message").textContent = error.message || String(error);
        }), 2500);
    }
    document.addEventListener("DOMContentLoaded", init, {once:true});
})();