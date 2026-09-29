/* SecureVault / VaultX — global JavaScript
   ==========================================================================
   Currently implements the mobile navigation toggle for the off-canvas
   sidebar. Kept small and focused; no frontend framework.
   ========================================================================== */

(function () {
    "use strict";

    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebar-overlay");
    var toggle = document.getElementById("menu-toggle");

    // Nothing to wire up if the shell elements are absent (e.g. auth pages).
    if (!sidebar || !overlay || !toggle) {
        return;
    }

    function openSidebar() {
        sidebar.classList.add("open");
        overlay.classList.add("open");
        toggle.setAttribute("aria-expanded", "true");
        toggle.setAttribute("aria-label", "Close navigation");
    }

    function closeSidebar() {
        sidebar.classList.remove("open");
        overlay.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open navigation");
    }

    // Toggle on hamburger click.
    toggle.addEventListener("click", function () {
        if (sidebar.classList.contains("open")) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    // Close when the dim overlay is clicked.
    overlay.addEventListener("click", closeSidebar);

    // Close when a navigation link is selected.
    sidebar.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", closeSidebar);
    });

    // Close on Escape.
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && sidebar.classList.contains("open")) {
            closeSidebar();
        }
    });
})();
