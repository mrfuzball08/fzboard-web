```
  ______ ______ ____   ___           _____  _____  
 |  ____|___  /|  _ \ / _ \    /\   |  __ \|  __ \ 
 | |__     / / | |_) | | | |  /  \  | |__) | |  | |
 |  __|   / /  |  _ <| | | | / /\ \ |  _  /| |  | |
 | |     / /__ | |_) | |_| |/ ____ \| | \ \| |__| |
 |_|    /_____||____/ \___//_/    \_\_|  \_\_____/ 
```
---
# FzBoard Web

> A web-based data analysis dashboard built with **Django 6.0** and **Svelte 5** (via **Vite**), styled with **Tailwind CSS v4** (Catppuccin Mocha), and designed for Docker deployment using **Bun**.
>
> *The dashboard interface is currently utilizing the **Svelte Islands** pattern — Svelte components are mounted into Django templates for dynamic widgets.*

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Infrastructure & Deployment](#infrastructure--deployment)
4. [Django Configuration](#django-configuration-fzboard)
5. [Application: `dashboard`](#application-dashboard)
   - [Models](#models)
   - [Forms](#forms)
   - [Views & URL Routing](#views--url-routing)
   - [Templates](#templates)
   - [Utilities](#utilities)
6. [Template Management (Formatos)](#template-management-formatos)
7. [Frontend & Styling](#frontend--styling)
   - [Vite & Svelte Pipeline](#vite--svelte-pipeline)
   - [Design System](#design-system)
   - [Custom Components (CSS)](#custom-components-css)
   - [Custom Utilities (CSS)](#custom-utilities-css)
8. [Authentication Flow](#authentication-flow)
9. [Testing](#testing)
   - [Test Structure](#test-structure)
   - [Volume Tests](#volume-tests)
   - [Running Tests](#running-tests)
10. [Dashboard (Mockup)](#dashboard-mockup)
11. [Diagrams](#diagrams)

---

## Tech Stack

| Layer            | Technology                    | Version |
|------------------|-------------------------------|---------|
| Backend          | Python / Django               | 6.0.1   |
| Database         | SQLite                        | —       |
| CSS Framework    | Tailwind CSS                  | 4.0.0 (via Vite)|
| Frontend         | Svelte + Vite + django-vite   | 5.0.0 / 6.0.0   |
| Font             | JetBrains Mono                | —       |
| Color Palette    | Catppuccin Mocha              | —       |
| Runtime          | Python 3.12 / Bun             | —       |
| Containerization | Docker + Docker Compose       | —       |

### Python Dependencies (`requirements.txt`)

```
asgiref==3.11.0
Django==6.0.1
django-vite>=3.0.0
pandas==3.0.1
sqlparse==0.5.5
tzdata==2025.3
```

### JS Dependencies (`package.json`)

```
vite ^6.0.0 (devDependency)
@sveltejs/vite-plugin-svelte ^5.0.0 (devDependency)
@tailwindcss/vite ^4.0.0 (devDependency)
svelte ^5.0.0 (devDependency)
tailwindcss ^4.0.0 (devDependency)
```

---

## Project Structure

```
fzboard-web/
├── fzboard/                        # Django project configuration
│   ├── __init__.py
│   ├── settings.py                 # Main settings (DB, apps, auth, etc.)
│   ├── urls.py                     # Root URL configuration
│   ├── asgi.py                     # ASGI entry point
│   └── wsgi.py                     # WSGI entry point
│
├── dashboard/                      # Main Django application
│   ├── __init__.py
│   ├── admin.py                    # Admin registration (User, TableTemplate, TemplateColumn)
│   ├── apps.py                     # App config (DashboardConfig)
│   ├── file_reading.py             # CSV/Excel → DataFrame utility
│   ├── forms.py                    # Auth forms + Template/Column forms
│   ├── models.py                   # User, TableTemplate, TemplateColumn
│   ├── urls.py                     # App-level URL routes (auth + template CRUD)
│   ├── views.py                    # View functions (auth + template management)
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py         # Custom User model
│   │   └── 0002_tabletemplate_templatecolumn.py
│   ├── tests/                      # Test suite (44 tests)
│   │   ├── __init__.py             # Imports all test modules
│   │   ├── test_models.py          # Model CRUD, constraints, cascades
│   │   ├── test_views.py           # View auth, search, ownership, timing
│   │   └── test_volume.py          # Volume/stress tests at 4 data scales
│   └── templates/
│       └── dashboard/
│           ├── _navbar.html        # Shared navigation bar partial
│           ├── dashboard.html      # Main dashboard page (mockup)
│           ├── login.html          # Login page
│           ├── register.html       # Registration page
│           ├── templates_list.html # Template listing with search
│           ├── template_create.html# New template creation form
│           ├── template_detail.html# Template detail + inline edit
│           └── template_delete.html# Delete confirmation page
│
├── frontend/                       # Vite/Svelte source
│   └── src/
│       ├── main.css                # Tailwind v4 directives + custom components
│       ├── main.js                 # Vite entry point (mounts Svelte islands)
│       └── components/
│           └── Dashboard.svelte    # Svelte component
│
├── static/                         # Compiled static assets
│   └── dist/                       # ← Generated by Vite (gitignored)
│
├── manage.py                       # Django management script
├── Dockerfile                      # Docker image definition
├── docker-compose.yml              # Docker Compose service definition
├── start.sh                        # Startup script (Bun run build/dev + Django server)
├── package.json                    # Bun / Vite config
├── vite.config.js                  # Vite Plugins (Tailwind v4, Svelte, manifest)
├── requirements.txt                # Python dependencies
├── db.sqlite3                      # SQLite database (gitignored)
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

---

## Infrastructure & Deployment

### Docker

The application is containerized using a **Dockerfile** based on `python:3.12-slim`:

1. **System dependencies** — Installs `curl`, `build-essential`, `libpq-dev`, and `unzip`.
2. **Bun runtime** — Installs **Bun** via install script (replacing Node.js/npm).
3. **Python dependencies** — Copies `requirements.txt` and runs `pip install`.
4. **JS dependencies** — Copies `package.json` and runs `bun install`.
5. **Entrypoint** — Runs `start.sh` which handles the Vite frontend build/dev server and starts the Django dev server.

**Exposed ports:** `8000` (Django) and `5173` (Vite HMR)

### Docker Compose (`docker-compose.yml`)

```yaml
services:
  web:
    build: .
    command: bash ./start.sh
    volumes:
      - .:/app                  # Bind mount for live code changes
      - /app/node_modules       # Prevent overwriting node_modules
    ports:
      - "8000:8000"             # Django
      - "5173:5173"             # Vite HMR Dev Server
    environment:
      - DEBUG=1
      - VITE_DEV_MODE=1         # Set to 1 to enable Vite HMR live dev server
```

### Startup Script (`start.sh`)

```bash
#!/bin/bash
bun run build                 # or 'bun run dev &' if VITE_DEV_MODE=1
python manage.py runserver 0.0.0.0:8000  # Django dev server
```

This ensures assets are compiled via **Vite**, dropping outputs into `static/dist/` with a manifest that `django-vite` reads. In HMR mode, Vite runs in the background.

---

## Django Configuration (`fzboard/`)

### `settings.py` — Key Configuration

| Setting                            | Value                             | Notes                                 |
|------------------------------------|-----------------------------------|---------------------------------------|
| `SECRET_KEY`                       | Insecure dev key                  | Must be replaced in production        |
| `DEBUG`                            | `True`                            | Development mode                      |
| `ALLOWED_HOSTS`                    | `['localhost', '127.0.0.1', '*']` | Open for development                  |
| `INSTALLED_APPS`                   | Includes `django_vite`            | Bridge for Vite asset serving         |
| `AUTH_USER_MODEL`                  | `'dashboard.User'`                | Custom user model                     |
| `DATABASES`                        | SQLite (`db.sqlite3`)             | File-based database                   |
| `STATIC_URL`                       | `/static/`                        | Static file URL prefix                |
| `STATICFILES_DIRS`                 | `[BASE_DIR / "static"]`           | Points to Vite-built assets directory |
| `DJANGO_VITE`                      | Config Dict                       | Points to manifest, port 5173, `dist/` prefix |
| `LOGIN_URL`                        | `/login/`                         | Redirect target for `@login_required` |
| `LOGIN_REDIRECT_URL`              | `/`                               | After login → dashboard               |
| `LOGOUT_REDIRECT_URL`             | `/login/`                         | After logout → login page             |

### `urls.py` — Root URL Config

```python
urlpatterns = [
    path('admin/', admin.site.urls),       # Django admin panel
    path('', include('dashboard.urls')),   # All app routes
]
```

All traffic (except `/admin/`) is delegated to the `dashboard` app.

---

## Application: `dashboard`

The `dashboard` is the single Django app containing all application logic.

### Models

**`dashboard/models.py`** — 3 models:

#### `User`

```python
class User(AbstractUser):
    pass
```

- Extends Django's `AbstractUser` with no additional fields (yet).
- Registered as the project's `AUTH_USER_MODEL`.
- Pattern allows easy future extension (profiles, roles, etc.).

#### `TableTemplate`

```python
class TableTemplate(models.Model):
    name        = CharField(max_length=255)
    description = TextField(blank=True, default='')
    owner       = ForeignKey(User, on_delete=CASCADE, related_name='templates')
    created_at  = DateTimeField(auto_now_add=True)
    updated_at  = DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ['name', 'owner']
```

- Represents a user-defined CSV format with named columns.
- Scoped per user via `owner` foreign key (cascade delete).
- Unique constraint prevents duplicate template names per user.

#### `TemplateColumn`

```python
class TemplateColumn(models.Model):
    DATA_TYPE_CHOICES = [
        ('text', 'Texto'), ('integer', 'Entero'), ('float', 'Decimal'),
        ('date', 'Fecha'), ('boolean', 'Booleano'),
        ('email', 'Correo Electrónico'), ('url', 'URL'),
    ]
    template  = ForeignKey(TableTemplate, on_delete=CASCADE, related_name='columns')
    name      = CharField(max_length=255)
    data_type = CharField(max_length=20, choices=DATA_TYPE_CHOICES, default='text')
    order     = PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
```

- Defines individual columns within a `TableTemplate`.
- Supports 7 data types.
- Ordered by the `order` field for consistent column positioning.

### Forms

**`dashboard/forms.py`** — 4 forms:

| Form                    | Type           | Purpose                                    |
|-------------------------|----------------|--------------------------------------------|
| `CustomUserCreationForm`| `UserCreationForm` | User registration (6 fields)           |
| `LoginForm`             | `Form`         | Username + password authentication         |
| `TableTemplateForm`     | `ModelForm`    | Template name and description editing      |
| `TemplateColumnForm`    | `ModelForm`    | Column name, data type, and order editing  |

All form widgets use the `form-input-hover` CSS class for consistent Catppuccin styling.

### Views & URL Routing

**`dashboard/urls.py`** — 9 routes:

| URL Pattern                    | View Function            | Name                | Auth |
|--------------------------------|--------------------------|---------------------|------|
| `/`                            | `dashboard()`            | `dashboard`         | Yes  |
| `/login/`                      | `login_view()`           | `login`             | No   |
| `/register/`                   | `register_view()`        | `register`          | No   |
| `/logout/`                     | `logout_view()`          | `logout`            | No   |
| `/formatos/`                   | `template_list()`        | `template_list`     | Yes  |
| `/formatos/crear/`             | `template_create()`      | `template_create`   | Yes  |
| `/formatos/<pk>/`              | `template_detail()`      | `template_detail`   | Yes  |
| `/formatos/<pk>/eliminar/`     | `template_delete()`      | `template_delete`   | Yes  |
| `/formatos/<pk>/descargar/`    | `template_download_csv()`| `template_download_csv` | Yes |

**View details:**

| View                    | Methods   | Behavior                                                                |
|-------------------------|-----------|-------------------------------------------------------------------------|
| `dashboard()`           | GET       | Renders the dashboard mockup. `@login_required`.                        |
| `register_view()`       | GET/POST  | Registration form → auto-login → redirect to `/`.                       |
| `login_view()`          | GET/POST  | Login form → authenticate → redirect to `/`.                            |
| `logout_view()`         | Any       | Logout → redirect to `/login/`.                                         |
| `template_list()`       | GET       | Lists user's templates. Supports `?q=` search filter.                   |
| `template_create()`     | GET/POST  | Create template + columns via `modelformset_factory`.                   |
| `template_detail()`     | GET/POST  | View template details + **inline editing** via `inlineformset_factory`. |
| `template_delete()`     | GET/POST  | Confirmation page → delete on POST.                                     |
| `template_download_csv()`| GET      | Generates and downloads a CSV file with column headers + type hints.    |

> **Localization:** All user-facing messages are in **Spanish**.

### Templates

All templates load Vite assets via `{% load django_vite %}` and `{% vite_asset "frontend/src/main.js" %}`. They share a common navigation bar via the `_navbar.html` partial.

| Template              | Purpose                                                        |
|-----------------------|----------------------------------------------------------------|
| `_navbar.html`        | Shared sticky navbar (logo, nav tabs, user info, logout)       |
| `login.html`          | Glassmorphism login card with animated gradient background     |
| `register.html`       | 6-field registration form with 2-column responsive grid        |
| `dashboard.html`      | Dashboard mockup (stats, file table, upload zone, storage bar) |
| `templates_list.html` | Template grid with search, glassmorphism cards, column counts  |
| `template_create.html`| New template form with dynamic column editor (JS formset)      |
| `template_detail.html`| Template detail view + toggleable inline edit mode             |
| `template_delete.html`| Delete confirmation page with warning styling                  |

### Utilities

**`dashboard/file_reading.py`**

```python
def read_file_to_dataframe(uploaded_file_path) -> pd.DataFrame
```

- Reads **CSV** or **Excel** (`.xlsx`, `.xls`) files → pandas DataFrame.
- Raises `ValueError` for unsupported file types.
- **Not yet integrated** into any view — prepared for future file upload features.

---

## Template Management (Formatos)

The template management system is the primary **functional feature** of the application. It enables users to define reusable CSV column structures.

### Workflow

```
┌─────────────┐    ┌──────────────────┐    ┌────────────────────┐
│ /formatos/  │───▶│ /formatos/crear/ │───▶│ /formatos/<pk>/    │
│ List view   │    │ Create form      │    │ Detail + Inline    │
│ (search, grid)   │ (name, desc,    │    │ Edit mode          │
└─────────────┘    │  columns)        │    └────────────────────┘
                   └──────────────────┘         │          │
                                                │          │
                                          ┌─────▼───┐  ┌───▼────────────┐
                                          │ Delete  │  │ Download CSV   │
                                          │ Confirm │  │ (headers +     │
                                          └─────────┘  │  type hints)   │
                                                       └────────────────┘
```

### Key Features

- **Template CRUD** — Full create, read, update, delete lifecycle.
- **Inline Editing** — Edit template name, description, and columns directly from the detail page via a toggleable edit mode.
- **Dynamic Column Editor** — JavaScript-driven add/remove columns with real-time numbering and counter updates.
- **CSV Export** — Download templates as `.csv` files with UTF-8 BOM for Excel compatibility.
- **Per-User Isolation** — Users only see and manage their own templates.
- **Column Types** — 7 supported data types: Texto, Entero, Decimal, Fecha, Booleano, Correo Electrónico, URL.

### Data Model Relationships

```
User (1) ──────── (N) TableTemplate (1) ──────── (N) TemplateColumn
  │                      │                                │
  │ CASCADE              │ name (unique per user)          │ name
  │                      │ description                     │ data_type (7 choices)
  │                      │ created_at / updated_at         │ order
  └──────────────────────┘                                └──────────────────
```

---

## Frontend & Styling

### Vite & Svelte Pipeline

```
frontend/src/main.js & main.css  →  [Vite]  →  static/dist/assets/
(includes Svelte & Tailwind v4)                  + manifest.json
```

| Bun Script | Command               | Purpose                                       |
|------------|-----------------------|-----------------------------------------------|
| `dev`      | `vite`                | Dev server on :5173 with HMR (Hot Reload)     |
| `build`    | `vite build`          | Compiles JS/CSS/Svelte to `static/dist/`      |
| `preview`  | `vite preview`        | Preview production build local server         |

**Svelte Islands Pattern:**
Instead of a Single Page Application (SPA), the project uses Svelte Islands. Django continues to route requests and render HTML templates structure. Dynamic components are mounted via `main.js` targeting specific `div` elements exposed by Django templates.

**Tailwind v4 Configuration:**
Instead of a `tailwind.config.js`, Tailwind CSS v4 is configured entirely within CSS via `@theme` and `@source` directives in `frontend/src/main.css`.

### Design System

The project uses the **Catppuccin Mocha** color scheme configured natively in CSS variables the `@theme` block of `main.css`:

| Token          | Hex       | Usage                        |
|----------------|-----------|------------------------------|
| `cat-base`     | `#1e1e2e` | Main background              |
| `cat-mantle`   | `#181825` | Sidebars / darker backgrounds|
| `cat-crust`    | `#11111b` | Darkest background           |
| `cat-surface0` | `#313244` | Cards / containers           |
| `cat-surface1` | `#45475a` | Soft borders / hover         |
| `cat-surface2` | `#585b70` | Intense hover                |
| `cat-text`     | `#cdd6f4` | Primary text                 |
| `cat-subtext0` | `#a6adc8` | Secondary text               |
| `cat-overlay0` | `#6c7086` | Disabled text / icons        |
| `cat-mauve`    | `#cba6f7` | **Primary accent** (purple)  |
| `cat-blue`     | `#89b4fa` | Information                  |
| `cat-green`    | `#a6e3a1` | Success                      |
| `cat-yellow`   | `#f9e2af` | Warning                      |
| `cat-peach`    | `#fab387` | Soft orange                  |
| `cat-red`      | `#f38ba8` | Error / danger               |
| `cat-pink`     | `#f5c2e7` | Secondary accent             |

**Typography:** JetBrains Mono — used for both `font-mono` and `font-sans`.

### Custom Components (CSS)

Defined in `frontend/src/main.css` under global styles:

| Class              | Description                                                 |
|--------------------|-------------------------------------------------------------|
| `.glass-card`      | Glassmorphism card (semi-transparent bg + backdrop blur)     |
| `.form-input`      | Base form input styling (dark bg, rounded, focus ring)       |
| `.form-input-hover`| Form input with hover effects (bg change, border, shadow)    |
| `.btn-primary`     | Gradient button (mauve → pink), scale-on-hover              |
| `.btn-secondary`   | Solid surface button with hover scale                       |
| `.auth-card`       | Auth page card (glassmorphism + max-width + hover shadow)   |
| `.logo`            | Gradient text logo (mauve → pink)                           |
| `.alert-success`   | Success message banner (green tinted)                       |
| `.alert-error`     | Error message banner (red tinted)                           |
| `.alert-info`      | Info message banner (blue tinted)                           |
| `.link-primary`    | Styled link (mauve → pink on hover, underline animation)    |
| `.field-group`     | Form field wrapper with spacing                             |
| `.field-label`     | Label styling (small, bold, uppercase, tracking)            |
| `.spinner`         | Animated loading spinner                                    |
| `.float-animation` | Vertical floating animation (6s cycle)                      |
| `.pulse-glow`      | Pulsing opacity animation (2s cycle)                        |
| `.errorlist`       | Django form error list styling (red, small, bulleted)       |

### Custom Utilities (CSS)

| Class            | Description                                            |
|------------------|--------------------------------------------------------|
| `.text-gradient` | Gradient text (mauve → pink), clip-to-text effect      |
| `.glow-mauve`    | Box shadow glow in mauve                               |
| `.glow-pink`     | Box shadow glow in pink                                |

---

## Authentication Flow

```
┌────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  /login/       │────▶│  Authenticate   │────▶│  / (Dashboard)   │
│  (LoginForm)   │     │  (Django Auth)  │     │  @login_required │
└────────────────┘     └─────────────────┘     └──────────────────┘
        ▲                                              │
        │  redirect                        logout (POST)
        ▼                                              ▼
┌────────────────┐                             ┌──────────────────┐
│  /register/    │                             │  /logout/        │
│  (UserCreation │────▶ auto-login ───────────▶│  redirect →      │
│   Form)        │                             │  /login/         │
└────────────────┘                             └──────────────────┘
```

1. **Unauthenticated users** accessing `/` are redirected to `/login/`.
2. **Registration** creates a user, auto-logs them in, and redirects to the dashboard.
3. **Login** authenticates against the `User` model and redirects to `/`.
4. **Logout** terminates the session and redirects to `/login/`.
5. **Sessions expire** after 1 hour or when the browser is closed.
6. **Password validation** via Django built-in validators.

---

## Testing

### Test Structure

The test suite lives in `dashboard/tests/` with **44 total tests** across 3 modules:

```
dashboard/tests/
├── __init__.py        # Re-exports all test classes
├── test_models.py     # 10 tests — Model CRUD, constraints, cascades
├── test_views.py      #  6 tests — View auth, search, isolation, timing
└── test_volume.py     # 28 tests — Volume/stress at 4 data scales
```

#### `test_models.py` — Model Tests

| Test Class           | Tests | Covers                                                  |
|----------------------|-------|---------------------------------------------------------|
| `UserModelTests`     | 4     | User creation, listing, `__str__`, query response time  |
| `TemplateModelTests` | 6     | `__str__`, column ordering, unique constraint, cascade deletes |

#### `test_views.py` — View Tests

| Test Class               | Tests | Covers                                                     |
|--------------------------|-------|------------------------------------------------------------|
| `TemplateListViewTests`  | 6     | Login redirect, authenticated access, ownership isolation, search filter, template count, HTTP response time |

### Volume Tests

`test_volume.py` tests performance at **4 different data scales**, each measuring query response times:

| Test Class                    | Users | Templates | Columns | Measurements                           |
|-------------------------------|-------|-----------|---------|----------------------------------------|
| `Volume50Users10TemplatesTest`  | 50    | 500       | 2,500   | All users, all templates, user templates, HTTP view |
| `Volume50Users30TemplatesTest`  | 50    | 1,500     | 7,500   | All users, all templates, user templates, HTTP view |
| `Volume100Users10TemplatesTest` | 100   | 1,000     | 5,000   | All users, all templates, user templates, HTTP view |
| `Volume100Users30TemplatesTest` | 100   | 3,000     | 15,000  | All users, all templates, user templates, HTTP view |

Each volume class includes 7 tests: data verification (user count, template count, column count) + 4 timed performance assertions.

**Performance results** (in-memory SQLite):

| Metric                  | 50u×10t  | 50u×30t  | 100u×10t | 100u×30t |
|-------------------------|----------|----------|----------|----------|
| All users query         | 0.0009s  | 0.0013s  | 0.0012s  | 0.0012s  |
| All templates query     | 0.0050s  | 0.0128s  | 0.0094s  | 0.0343s  |
| User templates query    | 0.0013s  | 0.0012s  | 0.0011s  | 0.0009s  |
| Template list HTTP view | 0.0091s  | 0.0185s  | 0.0084s  | 0.0196s  |

### Running Tests

```bash
# Run all 44 tests
sudo docker compose exec web python manage.py test dashboard -v 2

# Run only model tests
sudo docker compose exec web python manage.py test dashboard.tests.test_models -v 2

# Run only view tests
sudo docker compose exec web python manage.py test dashboard.tests.test_views -v 2

# Run only volume/stress tests
sudo docker compose exec web python manage.py test dashboard.tests.test_volume -v 2
```

---

## Dashboard Component

The dashboard page at `/` renders a **Svelte element**. A `div#svelte-dashboard` receives the `Dashboard.svelte` client-side component.

---

## Diagrams

### Request Flow

```
Browser Request
     │
     ▼
┌──────────────────────────────────────────────────────┐
│                     Django                           │
│                                                      │
│  fzboard/urls.py                                     │
│    ├── /admin/           → Django Admin              │
│    └── /*                → dashboard/urls.py         │
│                                                      │
│  dashboard/urls.py                                   │
│    ├── /                 → dashboard()         [auth] │
│    ├── /login/           → login_view()               │
│    ├── /register/        → register_view()            │
│    ├── /logout/          → logout_view()              │
│    ├── /formatos/        → template_list()     [auth] │
│    ├── /formatos/crear/  → template_create()   [auth] │
│    ├── /formatos/<pk>/   → template_detail()   [auth] │
│    ├── /formatos/<pk>/eliminar/  → template_delete()   [auth] │
│    └── /formatos/<pk>/descargar/ → template_download_csv() [auth]│
│                                                      │
│  Template Rendering                                  │
│    └── dashboard/templates/dashboard/*.html           │
│         └── {% vite_asset "frontend/src/main.js" %}  │
│                                                      │
└──────────────────────────────────────────────────────┘
     │
     ▼
  SQLite (db.sqlite3)
    ├── User
    ├── TableTemplate
    └── TemplateColumn
```

### Build Pipeline

```
┌────────────────────────┐      ┌─────────────────────────┐
│ frontend/src/          │      │ static/dist/            │
│   main.css             │───▶  │   assets/*.js           │
│   main.js              │ Vite │   assets/*.css          │
│   components/*.svelte  │      │   .vite/manifest.json   │
└────────────────────────┘      └─────────────────────────┘
         │                               │
         │  bun run dev/build            │  {% vite_asset %} via
         │                               │  django-vite
         ▼                               ▼
  vite.config.js                  HTML Templates
```

### Docker Architecture

```
┌──────────────────────────────────────────────┐
│  Docker Container (python:3.12-slim)         │
│                                              │
│  ┌───────────────┐   ┌───────────────────┐   │
│  │ vite          │   │ python manage.py  │   │
│  │ (HMR dev)     │   │   runserver       │   │
│  │ :5173         │   │   0.0.0.0:8000    │   │
│  └───────────────┘   └───────────────────┘   │
│          │                     │             │
│   Port 5173 ───────┐   Port 8000 ────────┐   │
└────────────────────┼─────────────────────┼───┘
                     │                     │
          Exposed → 5173:5173          8000:8000
                     │                     │
                Host Machine
```

---

*Updated: 2026-03-01*
