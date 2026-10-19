(function () {

    function getCurrentPage() {
        const path = window.location.pathname.split("/").pop();
        return path || "dashboard.html";
    }

    function createSidebar() {
        const currentPage = getCurrentPage();
        const sidebar = document.createElement("aside");
        sidebar.className = "app-sidebar";

        sidebar.innerHTML = `
            <div class="sidebar-header">
                <div class="sidebar-brand">
                    <div class="sidebar-brand-mark">V</div>
                    <div class="sidebar-brand-text">
                        <span class="sidebar-brand-title">Vul-Management</span>
                        <span class="sidebar-brand-version">Vulnerability Platform</span>
                    </div>
                </div>
                <button type="button" id="sidebar-toggle" class="sidebar-toggle" aria-label="Collapse sidebar" title="Collapse sidebar">‹</button>
            </div>

            <div class="sidebar-content">
                <div class="sidebar-section">
                    <a href="dashboard.html" class="sidebar-item ${currentPage === "dashboard.html" ? "active" : ""}">
                        <span class="sidebar-icon">▦</span><span class="sidebar-label">Dashboard</span>
                    </a>
                </div>

                <div class="sidebar-section">
                    <button type="button" class="sidebar-section-toggle sidebar-parent ${[
                        "equipment.html","operating-systems.html","applications.html","libraries.html"
                    ].includes(currentPage) ? "active" : ""}" data-sidebar-target="assets-menu">
                        <span class="sidebar-section-title"><span class="sidebar-icon">◈</span><span class="sidebar-label">Assets</span></span>
                        <span class="sidebar-chevron">›</span>
                    </button>
                    <div id="assets-menu" class="sidebar-submenu ${[
                        "equipment.html","operating-systems.html","applications.html","libraries.html"
                    ].includes(currentPage) ? "open" : ""}">
                        <a href="equipment.html" class="sidebar-subitem ${currentPage === "equipment.html" ? "active" : ""}">Equipment</a>
                        <a href="operating-systems.html" class="sidebar-subitem ${currentPage === "operating-systems.html" ? "active" : ""}">Operating Systems</a>
                        <a href="applications.html" class="sidebar-subitem ${currentPage === "applications.html" ? "active" : ""}">Applications</a>
                        <a href="libraries.html" class="sidebar-subitem ${currentPage === "libraries.html" ? "active" : ""}">Libraries</a>
                    </div>
                </div>

                <div class="sidebar-section">
                    <button type="button" class="sidebar-section-toggle sidebar-parent ${["nessus-manual-scan.html","nessus-scan-result.html","vulnerability-scan.html","scan-result.html","vulnerabilities.html"].includes(currentPage) ? "active" : ""}" data-sidebar-target="intelligence-menu">
                        <span class="sidebar-section-title"><span class="sidebar-icon">◉</span><span class="sidebar-label">Threat Intelligence</span></span>
                        <span class="sidebar-chevron">›</span>
                    </button>
                    <div id="intelligence-menu" class="sidebar-submenu ${["nessus-manual-scan.html","nessus-scan-result.html","vulnerability-scan.html","scan-result.html","vulnerabilities.html"].includes(currentPage) ? "open" : ""}">
                        <a href="nessus-manual-scan.html" class="sidebar-subitem ${currentPage === "nessus-manual-scan.html" ? "active" : ""}">Nessus Manual Scan</a>
                        <a href="nessus-scan-result.html" class="sidebar-subitem ${currentPage === "nessus-scan-result.html" ? "active" : ""}">Nessus Scan Result</a>
                        <a href="vulnerability-scan.html" class="sidebar-subitem ${currentPage === "vulnerability-scan.html" ? "active" : ""}">Vulnerability Scan</a>
                        <a href="scan-result.html" class="sidebar-subitem ${currentPage === "scan-result.html" ? "active" : ""}">Scan Result</a>
                        <a href="vulnerabilities.html" class="sidebar-subitem ${currentPage === "vulnerabilities.html" ? "active" : ""}">Vulnerabilities</a>
                    </div>
                </div>

                <div class="sidebar-section">
                    <button type="button" class="sidebar-section-toggle sidebar-parent" data-sidebar-target="reporting-menu">
                        <span class="sidebar-section-title"><span class="sidebar-icon">▤</span><span class="sidebar-label">Reporting</span></span>
                        <span class="sidebar-chevron">›</span>
                    </button>
                    <div id="reporting-menu" class="sidebar-submenu">
                        <a href="#" class="sidebar-subitem disabled" title="Coming soon">Dashboard</a>
                        <a href="#" class="sidebar-subitem disabled" title="Coming soon">Reports</a>
                    </div>
                </div>

                <div class="sidebar-divider"></div>

                <div class="sidebar-section">
                    <button type="button" class="sidebar-section-toggle sidebar-parent ${["vulnerability-feeds.html","telegram-feeds.html","telegram-settings.html","nessus-host-mapping.html","logs-events.html"].includes(currentPage) ? "active" : ""}" data-sidebar-target="administration-menu">
                        <span class="sidebar-section-title"><span class="sidebar-icon">⚙</span><span class="sidebar-label">Administration</span></span>
                        <span class="sidebar-chevron">›</span>
                    </button>
                    <div id="administration-menu" class="sidebar-submenu ${["vulnerability-feeds.html","telegram-feeds.html","telegram-settings.html","nessus-host-mapping.html","logs-events.html"].includes(currentPage) ? "open" : ""}">
                        <a href="vulnerability-feeds.html" class="sidebar-subitem ${currentPage === "vulnerability-feeds.html" ? "active" : ""}">Vulnerability Feeds</a>
                        <a href="telegram-feeds.html" class="sidebar-subitem ${currentPage === "telegram-feeds.html" ? "active" : ""}">Telegram Feeds</a>
                        <a href="telegram-settings.html" class="sidebar-subitem ${currentPage === "telegram-settings.html" ? "active" : ""}">Telegram Settings</a>
                        <a href="nessus-host-mapping.html" class="sidebar-subitem ${currentPage === "nessus-host-mapping.html" ? "active" : ""}">Nessus Host Mapping</a>
                        <a href="logs-events.html" class="sidebar-subitem ${currentPage === "logs-events.html" ? "active" : ""}">Logs &amp; Events</a>
                    </div>
                </div>
            </div>

            <div class="sidebar-footer"><span>Vul-Management</span><span>v3.1.0</span></div>
        `;

        document.body.prepend(sidebar);
        initializeSidebar();
    }

    function initializeSidebar() {
        const toggleButton = document.getElementById("sidebar-toggle");
        const body = document.body;

        if (toggleButton) {
            toggleButton.addEventListener("click", () => {
                body.classList.toggle("sidebar-collapsed");
                toggleButton.textContent = body.classList.contains("sidebar-collapsed") ? "›" : "‹";
            });
        }

        document.querySelectorAll(".sidebar-section-toggle").forEach((button) => {
            button.addEventListener("click", () => {
                const target = document.getElementById(button.dataset.sidebarTarget);
                if (!target) return;
                target.classList.toggle("open");
                button.classList.toggle("expanded");
            });
        });

        document.querySelectorAll(".sidebar-submenu").forEach((submenu) => {
            const parent = document.querySelector(`[data-sidebar-target="${submenu.id}"]`);
            if (submenu.classList.contains("open") && parent) parent.classList.add("expanded");
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", createSidebar);
    } else {
        createSidebar();
    }
})();