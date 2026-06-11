/*jslint browser, single, long */

// Override API base URL for the web UI.
// Automatically uses the same host where the web UI is served.
// You can manually override by setting window.OOBIR_API_BASE before app.js.
if (!window.OOBIR_API_BASE) {
    window.OOBIR_API_BASE = window.location.origin;
}
window.CONFIG = window.CONFIG || {};
window.CONFIG.API_BASE_URL = window.OOBIR_API_BASE;
