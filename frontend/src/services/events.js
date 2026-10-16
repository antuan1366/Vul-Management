(() => {
    const $ = id => document.getElementById(id);
    let events = [];
    let expanded = new Set();
    let timer = null;

    function esc(value) {
        return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
    }
    function date(value) {
        if (!value) return "—";
        const parsed = new Date(value);
        return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString();
    }
    function duration(value) {
        return value === null || value === undefined ? "—" : Number(value).toLocaleString() + " ms";
    }
    function render() {
        $("events-count").textContent = events.length + " Events";
        $("events-error-count").textContent = "Errors: " + events.filter(x => ["ERROR","CRITICAL"].includes(x.level)).length;
        $("events-warning-count").textContent = "Warnings: " + events.filter(x => x.level === "WARNING").length;
        $("events-latest").textContent = "Latest event: " + (events.length ? date(events[0].created_at) : "—");
        const body = $("events-body");
        if (!events.length) {
            body.innerHTML = '<tr><td colspan="8">No events match the selected filters.</td></tr>';
            return;
        }
        body.innerHTML = events.map(item => {
            const id = Number(item.id);
            const open = expanded.has(id);
            const details = [
                "Event ID: " + item.id,
                "Correlation ID: " + (item.correlation_id || "—"),
                "Scan run ID: " + (item.scan_run_id ?? "—"),
                "CVE: " + (item.cve_id || "—"),
                "",
                item.details || "No additional details were recorded."
            ].join("\n");
            return '<tr class="event-row" data-event-id="' + id + '">' +
                '<td title="' + esc(item.created_at) + '">' + esc(date(item.created_at)) + '</td>' +
                '<td><span class="event-pill ' + esc(item.level) + '">' + esc(item.level) + '</span></td>' +
                '<td>' + esc(item.category) + '</td>' +
                '<td><strong>' + esc(item.component) + '</strong><div class="event-muted">' + esc(item.event) + '</div></td>' +
                '<td class="event-message">' + esc(item.message) + '</td>' +
                '<td>' + esc(item.cve_id || "—") + '</td>' +
                '<td>' + esc(item.scan_run_id ?? "—") + '</td>' +
                '<td>' + esc(duration(item.duration_ms)) + '</td></tr>' +
                (open ? '<tr class="event-detail-row"><td colspan="8"><div class="event-details">' + esc(details) + '</div></td></tr>' : '');
        }).join("");
    }
    async function load() {
        const params = new URLSearchParams({
            q: $("events-search").value.trim(),
            level: $("events-level").value,
            category: $("events-category").value,
            limit: $("events-limit").value
        });
        if ($("events-cve").value.trim()) params.set("cve_id", $("events-cve").value.trim());
        if ($("events-run").value) params.set("scan_run_id", $("events-run").value);
        try {
            const data = await apiRequest("/api/events?" + params.toString());
            events = data.items || [];
            const ids = new Set(events.map(x => Number(x.id)));
            expanded = new Set([...expanded].filter(id => ids.has(id)));
            $("events-message").textContent = "Showing " + events.length + " of " + data.total + " matching events. Updates automatically every 5 seconds.";
            render();
        } catch (error) {
            $("events-message").textContent = "Could not load events: " + (error.message || error);
            $("events-body").innerHTML = '<tr><td colspan="8">Event API is unavailable. Check the backend and retry.</td></tr>';
        }
    }
    function exportCsv() {
        const columns = ["id","created_at","level","category","component","event","message","details","correlation_id","cve_id","scan_run_id","duration_ms"];
        const quote = value => '"' + String(value ?? "").replace(/"/g, '""') + '"';
        const csv = [columns.join(","), ...events.map(item => columns.map(key => quote(item[key])).join(","))].join("\r\n");
        const url = URL.createObjectURL(new Blob(["\ufeff", csv], {type:"text/csv;charset=utf-8"}));
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "vul-management-events.csv";
        anchor.click();
        URL.revokeObjectURL(url);
    }
    ["events-search","events-level","events-category","events-cve","events-run","events-limit"].forEach(id => {
        $(id).addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(load, 250); });
        $(id).addEventListener("change", load);
    });
    $("events-body").addEventListener("click", event => {
        const row = event.target.closest("[data-event-id]");
        if (!row) return;
        const id = Number(row.dataset.eventId);
        if (expanded.has(id)) expanded.delete(id); else expanded.add(id);
        render();
    });
    $("events-export").addEventListener("click", exportCsv);
    load();
    setInterval(load, 5000);
})();
