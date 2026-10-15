(() => {
    const $ = (id) => document.getElementById(id);
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

    function openModal(id) {
        const modal = $(id);
        if (!modal) return;
        modal.hidden = false;
        document.body.style.overflow = "hidden";
        const first = modal.querySelector("input:not(:disabled),select:not(:disabled),button:not(:disabled)");
        if (first) first.focus();
    }
    function closeModal(id) {
        const modal = $(id);
        if (!modal) return;
        modal.hidden = true;
        if (![...document.querySelectorAll(".scan-modal-backdrop")].some(x => !x.hidden)) {
            document.body.style.overflow = "";
        }
    }

    function syncScheduleControls() {
        const enabled = $("scan-schedule-enabled").checked;
        $("scan-schedule-frequency").disabled = !enabled;
        $("scan-schedule-time").disabled = !enabled;
        $("scan-schedule-day").disabled = !enabled || $("scan-schedule-frequency").value !== "weekly";
    }

    async function loadSchedule() {
        const schedule = await req("/api/threat-intelligence/schedule");
        $("scan-schedule-enabled").checked = Boolean(schedule.enabled);
        $("scan-schedule-frequency").value = schedule.frequency || "daily";
        $("scan-schedule-time").value = schedule.scan_time || "02:00";
        $("scan-schedule-day").value = String(schedule.day_of_week ?? 0);
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
            const log = run.error_message || (run.status === "running" || run.status === "pending" ? "Scan in progress…" : "Completed without reported errors");
            return '<tr><td>'+(i+1)+'</td><td>'+esc(run.mode === "from_date" ? "From date" : "New messages")+'</td><td>'+esc(date(run.started_at || run.date))+'</td><td>'+esc(date(run.finished_at))+'</td><td><span class="scan-log-status">'+esc(pretty(run.status))+'</span></td><td>'+esc(run.channels_processed)+' / '+esc(run.channels_total)+'</td><td>'+esc(run.messages_processed)+'</td><td>'+esc(run.cve_occurrences)+'</td><td title="'+esc(log)+'">'+esc(log.length > 150 ? log.slice(0,147)+"…" : log)+'</td></tr>';
        }).join("");
    }

    function renderProgress(run) {
        const wrap = $("scan-progress-wrap");
        if (!run) {
            wrap.hidden = true;
            return;
        }
        wrap.hidden = false;
        const running = ["pending","running"].includes(run.status);
        const total = Number(run.channels_total || 0);
        const done = Number(run.channels_processed || 0);
        const pct = running ? (total > 0 ? Math.min(100, Math.round(done / total * 100)) : 0) : 100;
        $("scan-progress-label").textContent = running ? (run.status === "pending" ? "Scan is queued…" : "Scan is running…") : "Scan finished";
        $("scan-progress-value").textContent = running ? (total > 0 ? pct + "%" : "Starting") : pretty(run.status);
        $("scan-progress-detail").textContent = "Channels processed: " + done + " of " + total + " · Messages: " + (run.messages_processed || 0) + " · CVE occurrences: " + (run.cve_occurrences || 0) + (run.error_message ? " · " + run.error_message : "");
        const bar = $("scan-progress-bar");
        bar.classList.toggle("indeterminate", running && total === 0);
        bar.style.width = (running && total === 0) ? "35%" : pct + "%";
        wrap.querySelector('[role="progressbar"]').setAttribute("aria-valuenow", String(pct));
        if (!running && activeRunId === run.id) {
            $("scan-now-message").textContent = "Scan " + pretty(run.status).toLowerCase() + ". " + (run.cve_occurrences || 0) + " CVE occurrences found. Details are recorded in Last Scan Log.";
            activeRunId = null;
            $("start-scan-submit").disabled = false;
            $("start-scan-submit").textContent = "Start Scan";
        }
    }

    async function loadRuns() {
        const data = await req("/api/threat-intelligence/scan-runs?limit=100");
        const items = data.items || [];
        renderRuns(items);
        const current = activeRunId ? items.find(x => x.id === activeRunId) : items.find(x => ["pending","running"].includes(x.status));
        if (current) renderProgress(current);
    }

    async function startScan(event) {
        event.preventDefault();
        const button = $("start-scan-submit");
        const message = $("scan-now-message");
        const rawDate = $("scan-start-date").value;
        if (!rawDate) {
            message.textContent = "Please select a starting date and time.";
            return;
        }
        const startDate = new Date(rawDate);
        if (Number.isNaN(startDate.getTime())) {
            message.textContent = "The selected date/time is invalid.";
            return;
        }
        button.disabled = true;
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
                body: JSON.stringify({mode: "from_date", start_date: startDate.toISOString()})
            });
            activeRunId = result.scan_run_id;
            message.textContent = "Scan #" + result.scan_run_id + " started. Progress is shown below.";
            await loadRuns();
        } catch (error) {
            message.textContent = error.message || String(error);
            $("scan-progress-label").textContent = "Could not start scan";
            $("scan-progress-value").textContent = "Failed";
            $("scan-progress-detail").textContent = message.textContent;
            $("scan-progress-wrap").hidden = false;
            button.disabled = false;
            button.textContent = "Start Scan";
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
            syncScheduleControls();
        } catch (error) {
            $("scan-schedule-message").textContent = error.message || String(error);
        } finally {
            button.disabled = false;
        }
    }

    async function refresh() {
        const results = await Promise.allSettled([loadSchedule(), loadRuns()]);
        const failed = results.find(x => x.status === "rejected");
        if (failed) {
            $("scan-schedule-message").textContent = failed.reason?.message || String(failed.reason);
            $("scan-log-body").innerHTML = '<tr><td colspan="9">Could not load scan history: '+esc(failed.reason?.message || failed.reason)+'</td></tr>';
        }
    }

    function init() {
        $("open-scan-now").addEventListener("click", () => {
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            $("scan-start-date").value = now.toISOString().slice(0,16);
            openModal("scan-now-modal");
        });
        $("open-scheduled-scan").addEventListener("click", () => openModal("scheduled-scan-modal"));
        document.querySelectorAll("[data-close-modal]").forEach(button => {
            button.addEventListener("click", () => closeModal(button.dataset.closeModal));
        });
        document.querySelectorAll(".scan-modal-backdrop").forEach(modal => {
            modal.addEventListener("click", event => {
                if (event.target === modal) closeModal(modal.id);
            });
        });
        document.addEventListener("keydown", event => {
            if (event.key === "Escape") {
                document.querySelectorAll(".scan-modal-backdrop:not([hidden])").forEach(modal => closeModal(modal.id));
            }
        });
        $("scan-schedule-enabled").addEventListener("change", syncScheduleControls);
        $("scan-schedule-frequency").addEventListener("change", syncScheduleControls);
        $("scan-schedule-form").addEventListener("submit", saveSchedule);
        $("scan-now-form").addEventListener("submit", startScan);
        refresh();
        window.setInterval(() => loadRuns().catch(error => {
            $("scan-now-message").textContent = error.message || String(error);
        }), 2500);
    }
    document.addEventListener("DOMContentLoaded", init, {once:true});
})();