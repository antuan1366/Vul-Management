
let feeds = [];
let editingFeedId = null;

function escapeFeedHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function feedTypeLabel(type) {
    const labels = {
        nvd_cpe: "NVD CPE",
        nvd_cve: "NVD CVE",
        cisa_kev: "CISA KEV",
        osv: "OSV",
        custom: "Custom"
    };
    return labels[type] || type;
}

function formatFeedTest(feed) {
    if (!feed.last_test_status) {
        return "Not tested";
    }
    const status = feed.last_test_status === "success" ? "Success" : "Failed";
    return '<span title="' +
        escapeFeedHtml(feed.last_test_message || status) +
        '">' + status + "</span>";
}

function renderFeeds() {
    const body = document.getElementById("feeds-table-body");
    const count = document.getElementById("feed-count");

    if (!body) {
        return;
    }

    if (count) {
        count.textContent =
            feeds.length + " Feed" + (feeds.length === 1 ? "" : "s");
    }

    if (!feeds.length) {
        body.innerHTML =
            '<tr><td colspan="8" class="empty-cell">No feeds configured.</td></tr>';
        return;
    }

    body.innerHTML = feeds.map(function (feed, index) {
        return [
            "<tr>",
            "<td>" + (index + 1) + "</td>",
            "<td><strong>" + escapeFeedHtml(feed.name) + "</strong>",
            '<div class="section-description">' + escapeFeedHtml(feed.url) + "</div></td>",
            "<td>" + escapeFeedHtml(feedTypeLabel(feed.feed_type)) + "</td>",
            "<td>" + escapeFeedHtml(feed.method) + "</td>",
            "<td>" + (feed.enabled ? "Enabled" : "Disabled") + "</td>",
            "<td>" + escapeFeedHtml(feed.auth_type) +
                (feed.has_api_key ? " (configured)" : "") + "</td>",
            "<td>" + formatFeedTest(feed) + "</td>",
            '<td><div class="table-actions">',
            '<button type="button" class="secondary-button small-button" data-action="test" data-id="' +
                feed.id + '">Test</button>',
            '<button type="button" class="secondary-button small-button" data-action="edit" data-id="' +
                feed.id + '">Edit</button>',
            '<button type="button" class="danger-button small-button" data-action="delete" data-id="' +
                feed.id + '">Delete</button>',
            "</div></td>",
            "</tr>"
        ].join("");
    }).join("");
}

async function loadFeeds() {
    const body = document.getElementById("feeds-table-body");

    if (body) {
        body.innerHTML =
            '<tr><td colspan="8" class="loading-cell">Loading feeds...</td></tr>';
    }

    try {
        feeds = await apiRequest("/api/feeds");
        renderFeeds();
    } catch (error) {
        if (body) {
            body.innerHTML =
                '<tr><td colspan="8" class="error-cell">' +
                escapeFeedHtml(error.message) +
                "</td></tr>";
        }
    }
}

function openFeedModal(feed) {
    const modal = document.getElementById("feed-modal");
    const title = document.getElementById("feed-form-title");

    editingFeedId = feed ? feed.id : null;
    title.textContent = feed ? "Edit Feed" : "Add Feed";

    document.getElementById("feed_name").value = feed?.name || "";
    document.getElementById("feed_type").value = feed?.feed_type || "nvd_cpe";
    document.getElementById("feed_url").value = feed?.url || "";
    document.getElementById("feed_method").value = feed?.method || "GET";
    document.getElementById("feed_auth_type").value = feed?.auth_type || "none";
    document.getElementById("feed_api_key").value = "";
    document.getElementById("feed_timeout").value = feed?.timeout_seconds || 15;
    document.getElementById("feed_enabled").checked = feed?.enabled ?? true;
    document.getElementById("feed_description").value = feed?.description || "";

    updateApiKeyVisibility();

    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
}

function closeFeedModal() {
    const modal = document.getElementById("feed-modal");
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    editingFeedId = null;
}

function updateApiKeyVisibility() {
    const field = document.getElementById("api-key-field");
    const authType = document.getElementById("feed_auth_type").value;
    field.style.display = authType === "none" ? "none" : "flex";
}

async function saveFeed(event) {
    event.preventDefault();

    const payload = {
        name: document.getElementById("feed_name").value.trim(),
        feed_type: document.getElementById("feed_type").value,
        url: document.getElementById("feed_url").value.trim(),
        method: document.getElementById("feed_method").value,
        auth_type: document.getElementById("feed_auth_type").value,
        timeout_seconds: Number(document.getElementById("feed_timeout").value),
        enabled: document.getElementById("feed_enabled").checked,
        description: document.getElementById("feed_description").value.trim() || null
    };

    const secret = document.getElementById("feed_api_key").value;
    if (secret) {
        payload.api_key = secret;
    }

    if (editingFeedId && payload.auth_type === "none") {
        payload.clear_api_key = true;
    }

    try {
        if (editingFeedId) {
            await apiRequest("/api/feeds/" + editingFeedId, {
                method: "PUT",
                body: JSON.stringify(payload)
            });
        } else {
            await apiRequest("/api/feeds", {
                method: "POST",
                body: JSON.stringify(payload)
            });
        }

        closeFeedModal();
        await loadFeeds();
    } catch (error) {
        alert(error.message);
    }
}

async function handleFeedAction(event) {
    const button = event.target.closest("button[data-action]");
    if (!button) {
        return;
    }

    const feedId = Number(button.dataset.id);
    const feed = feeds.find(function (item) {
        return item.id === feedId;
    });

    if (!feed) {
        return;
    }

    const action = button.dataset.action;

    if (action === "edit") {
        openFeedModal(feed);
        return;
    }

    if (action === "test") {
        button.disabled = true;
        button.textContent = "Testing...";

        try {
            await apiRequest("/api/feeds/" + feedId + "/test", {
                method: "POST"
            });
            await loadFeeds();
        } catch (error) {
            alert(error.message);
        } finally {
            button.disabled = false;
            button.textContent = "Test";
        }
        return;
    }

    if (action === "delete") {
        if (!confirm('Delete feed "' + feed.name + '"?')) {
            return;
        }

        try {
            await apiRequest("/api/feeds/" + feedId, {
                method: "DELETE"
            });
            await loadFeeds();
        } catch (error) {
            alert(error.message);
        }
    }
}

function initializeFeedsPage() {
    document.getElementById("add-feed-button")?.addEventListener(
        "click",
        function () { openFeedModal(); }
    );

    document.getElementById("test-identification-feeds-button")?.addEventListener(
        "click",
        async function () {
            const button = this;
            const identificationFeeds = feeds.filter(function (feed) {
                return feed.feed_type === "nvd_cpe" || feed.feed_type === "osv";
            });
            if (!identificationFeeds.length) {
                alert("No NVD CPE or OSV feed is configured.");
                return;
            }

            button.disabled = true;
            button.textContent = "Testing...";
            try {
                for (const feed of identificationFeeds) {
                    await apiRequest("/api/feeds/" + feed.id + "/test", { method: "POST" });
                }
                await loadFeeds();
            } catch (error) {
                alert(error.message);
            } finally {
                button.disabled = false;
                button.textContent = "Test Identification Feeds";
            }
        }
    );

    document.getElementById("close-feed-modal")?.addEventListener(
        "click",
        closeFeedModal
    );

    document.getElementById("cancel-feed-button")?.addEventListener(
        "click",
        closeFeedModal
    );

    document.getElementById("feed-form")?.addEventListener(
        "submit",
        saveFeed
    );

    document.getElementById("feed_auth_type")?.addEventListener(
        "change",
        updateApiKeyVisibility
    );

    document.getElementById("feeds-table-body")?.addEventListener(
        "click",
        handleFeedAction
    );

    document.getElementById("feed-modal")?.addEventListener(
        "click",
        function (event) {
            if (event.target.id === "feed-modal") {
                closeFeedModal();
            }
        }
    );

    document.addEventListener("keydown", function (event) {
        if (
            event.key === "Escape" &&
            document.getElementById("feed-modal")?.classList.contains("is-open")
        ) {
            closeFeedModal();
        }
    });

    loadFeeds();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeFeedsPage);
} else {
    initializeFeedsPage();
}
