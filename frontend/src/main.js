import { mount } from 'svelte'

// Global styles — Tailwind v4 + custom Catppuccin Mocha design system
import './main.css'

// ─── Svelte Islands ──────────────────────────────────────────────────────────
// Import Svelte components and mount them into specific Django-rendered DOM
// elements.  Each mount is guarded so components only activate when the
// corresponding element is present on the current page.

import Navbar from './components/Navbar.svelte'
import Dashboard from './components/Dashboard.svelte'
import LoginForm from './components/LoginForm.svelte'
import RegisterForm from './components/RegisterForm.svelte'
import TemplateForm from './components/TemplateForm.svelte'

// Navbar widget (mounted inside _navbar.html across all pages)
const navbarEl = document.getElementById('svelte-navbar')
if (navbarEl) {
  mount(Navbar, {
    target: navbarEl,
    props: {
        activeNav: navbarEl.dataset.activeNav || '',
        username: navbarEl.dataset.username || '',
        email: navbarEl.dataset.email || '',
        csrfToken: navbarEl.dataset.csrfToken || ''
    }
  })
}

// Dashboard widget (mounted inside dashboard.html)
const dashboardEl = document.getElementById('svelte-dashboard')
if (dashboardEl) {
  mount(Dashboard, { target: dashboardEl })
}

// Login Form widget
const loginEl = document.getElementById('svelte-login-form')
if (loginEl) {
    mount(LoginForm, {
        target: loginEl,
        props: {
            csrf: loginEl.dataset.csrf || '',
            errorsJson: loginEl.dataset.errors || ''
        }
    })
}

// Register Form widget
const registerEl = document.getElementById('svelte-register-form')
if (registerEl) {
    mount(RegisterForm, {
        target: registerEl,
        props: {
            csrf: registerEl.dataset.csrf || '',
            errorsJson: registerEl.dataset.errors || ''
        }
    })
}

// Template Create/Edit Form widget
const templateFormEl = document.getElementById('svelte-template-form')
if (templateFormEl) {
    const d = window.__TEMPLATE_DATA__ || {};
    mount(TemplateForm, {
        target: templateFormEl,
        props: {
            csrf: d.csrf || templateFormEl.dataset.csrf || '',
            errorsJson: d.errors || templateFormEl.dataset.errors || '',
            formsetErrorsJson: d.formsetErrors || templateFormEl.dataset.formsetErrors || '',
            initialTitle: d.initialTitle || templateFormEl.dataset.initialTitle || '',
            initialDesc: d.initialDesc || templateFormEl.dataset.initialDesc || '',
            initialColumnsJson: d.initialColumns || templateFormEl.dataset.initialColumns || '[]',
            dataTypeChoicesJson: d.dataTypeChoices || templateFormEl.dataset.dataTypeChoices || '[]'
        }
    })
}
