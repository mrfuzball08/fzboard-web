// Global styles — Tailwind v4 + custom Catppuccin Mocha design system
import './main.css'

// ─── Svelte Islands ──────────────────────────────────────────────────────────
// Import Svelte components and mount them into specific Django-rendered DOM
// elements.  Each mount is guarded so components only activate when the
// corresponding element is present on the current page.

// Dashboard widget (mounted inside dashboard.html)
import Dashboard from './components/Dashboard.svelte'

const dashboardEl = document.getElementById('svelte-dashboard')
if (dashboardEl) {
  new Dashboard({ target: dashboardEl })
}
