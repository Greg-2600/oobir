// Override API base URL for the web UI
// Automatically uses the same host as the web UI is served from
// You can manually override by setting window.OOBIR_API_BASE before loading app.js
if (!window.OOBIR_API_BASE) {
    window.OOBIR_API_BASE = window.location.protocol + '//' + window.location.hostname + ':8000';
}
