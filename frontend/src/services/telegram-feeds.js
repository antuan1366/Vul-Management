(() => {
    const $ = (id) => document.getElementById(id);
    let feeds = [];
    function esc(value) {
        return String(value ?? "").replace(/[&<>"']/g, (c) => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
        }[c]));
    }
    async function req(url, options) { return apiRequest(url, options); }
    function showError(error) { $("telegram-feed-error").textContent = error?.message || String(error); }
    async function loadFeeds() {
        $("telegram-feed-error").textContent = "";
        const data = await req("/api/threat-intelligence/feeds");
        feeds = data.items || [];
        $("telegram-feed-count").textContent = data.total + " Channels";
        $("telegram-feeds-body").innerHTML = feeds.map((feed, index) =>
            '<tr><td>' + (index + 1) + '</td><td>' + esc(feed.name) + '</td>' +
            '<td><a href="https://t.me/' + encodeURIComponent(feed.channel_username) + '" target="_blank" rel="noopener">@' + esc(feed.channel_username) + '</a></td>' +
            '<td>' + (feed.enabled ? "Enabled" : "Disabled") + '</td><td>' + (feed.last_message_id ?? "—") + '</td>' +
            '<td><div class="telegram-actions"><button type="button" class="secondary-button" data-action="toggle" data-id="' + feed.id + '">' +
            (feed.enabled ? "Disable" : "Enable") + '</button><button type="button" class="secondary-button" data-action="delete" data-id="' + feed.id + '">Delete</button></div></td></tr>'
        ).join("") || '<tr><td colspan="6">No Telegram channels configured. Add a public channel above.</td></tr>';
    }
    async function handleAction(action, id) {
        const feed = feeds.find((item) => item.id === Number(id));
        if (!feed) return;
        if (action === "toggle") {
            await req("/api/threat-intelligence/feeds/" + id, { method: "PUT", body: JSON.stringify({ enabled: !feed.enabled }) });
        } else if (action === "delete") {
            if (!window.confirm("Delete this Telegram feed? Existing scan results will be kept.")) return;
            await req("/api/threat-intelligence/feeds/" + id, { method: "DELETE" });
        }
        await loadFeeds();
    }
    $("telegram-feed-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        $("telegram-feed-error").textContent = "";
        try {
            const name = $("telegram-feed-name").value.trim();
            const channel = $("telegram-feed-channel").value.trim().replace(/^@/, "");
            if (!name || !channel) throw new Error("Enter both a display name and a public channel username.");
            await req("/api/threat-intelligence/feeds", { method: "POST", body: JSON.stringify({ name, channel_username: channel, enabled: true }) });
            $("telegram-feed-form").reset();
            await loadFeeds();
        } catch (error) { showError(error); }
    });
    $("telegram-feeds-body").addEventListener("click", async (event) => {
        const button = event.target.closest("[data-action]");
        if (!button) return;
        try { await handleAction(button.dataset.action, button.dataset.id); } catch (error) { showError(error); }
    });
    $("telegram-refresh").addEventListener("click", () => loadFeeds().catch(showError));
    loadFeeds().catch(showError);
})();