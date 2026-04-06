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
import DatasetUploadWizard from './components/DatasetUploadWizard.svelte'

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

// Dataset Upload Wizard widget
const uploadWizardEl = document.getElementById('svelte-upload-wizard')
if (uploadWizardEl) {
    const d = window.__UPLOAD_DATA__ || {};
    mount(DatasetUploadWizard, {
        target: uploadWizardEl,
        props: {
            csrf: d.csrf || '',
            datasetPk: d.datasetPk || 0,
            templateName: d.templateName || '',
            columns: d.columns || [],
            mappingUrl: d.mappingUrl || '',
            uploadUrl: d.uploadUrl || '',
            hasExistingData: d.hasExistingData || false,
            existingRowCount: d.existingRowCount || 0,
        }
    })
}

// Report Viewer widget (mounted inside report_detail.html)
import ReportViewer from './components/ReportViewer.svelte'
const viewerEl = document.getElementById('svelte-report-viewer')
if (viewerEl) {
    const d = window.__VIEWER_DATA__ || {};
    mount(ReportViewer, {
        target: viewerEl,
        props: {
            widgetResults: d.widgetResults || [],
            widgetsMeta: d.widgetsMeta || [],
        }
    })
}

// Report Builder widget (mounted inside report_builder.html)
import ReportBuilder from './components/ReportBuilder.svelte'
const builderEl = document.getElementById('svelte-report-builder')
if (builderEl) {
    const d = window.__BUILDER_DATA__ || {};
    mount(ReportBuilder, {
        target: builderEl,
        props: {
            csrf: d.csrf || '',
            reportPk: d.reportPk || 0,
            reportName: d.reportName || '',
            datasetName: d.datasetName || '',
            templateName: d.templateName || '',
            fields: d.fields || [],
            widgets: d.widgets || [],
            filters: d.filters || [],
        }
    })
}
