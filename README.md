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

> A sophisticated web-based data analysis and reporting platform built with **Django 6.0** and **Svelte 5** (via **Vite**). Styled precisely with **Tailwind CSS v4** (Catppuccin Mocha), and containerized for deployment utilizing **Bun**.
>
> *The dashboard interface utilizes the Svelte Islands pattern to mount highly dynamic widgets natively within the Django architecture.*

---

## Table of Contents

1. [Architectural Stack](#architectural-stack)
2. [Project Structure](#project-structure)
3. [Infrastructure & Deployment](#infrastructure--deployment)
4. [Continuous Integration (CI)](#continuous-integration-ci)
5. [Application: Dashboard](#application-dashboard)
   - [Core Models](#core-models)
   - [Services & Processing](#services--processing)
   - [Views & Routing](#views--routing)
6. [Data Pipeline](#data-pipeline)
7. [Query Engine & Reporting](#query-engine--reporting)
8. [Frontend & Styling](#frontend--styling)
9. [Authentication Flow](#authentication-flow)
10. [Testing Suite](#testing-suite)

---

## Architectural Stack

| Layer            | Technology                    | Version |
|------------------|-------------------------------|---------|
| Backend          | Python / Django               | 6.0.1   |
| Database         | SQLite                        | —       |
| Data Processing  | Pandas                        | 3.0.1   |
| CSS Framework    | Tailwind CSS                  | 4.0.0 (via Vite)|
| Frontend         | Svelte + Vite + django-vite   | 5.0.0 / 6.0.0   |
| Visualization    | Chart.js                      | 4.4.x   |
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
dotenv==0.9.9
python-dotenv==1.2.2
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
chart.js ^4.4.0
```

---

## Project Structure

```
fzboard-web/
├── .github/ workflows/             # Continuous Integration Pipelines
│   ├── docker-build.yml
│   └── django-tests.yml
│
├── fzboard/                        # Django project configuration
│   ├── settings.py                 # Main configuration parameters
│   └── urls.py                     # Root URL routing
│
├── dashboard/                      # Core Django application domain
│   ├── models.py                   # ORM schema designs
│   ├── views.py                    # Controllers and HTTP endpoints
│   ├── forms.py                    # Form definitions
│   ├── services/                   # Business logic and processing
│   │   ├── import_readers.py       # File parsing (CSV/Excel)
│   │   ├── import_mapping.py       # Heuristic column mappings
│   │   ├── import_validation.py    # Strict data-type verification
│   │   ├── import_executor.py      # Batch database inserts
│   │   ├── report_query.py         # Pandas analytical query engine
│   │   └── report_validation.py    # Widget configuration schemas
│   ├── tests/                      # Automated Test suite
│   │   ├── test_models.py          # Data constraints
│   │   ├── test_views.py           # Endpoint integration
│   │   ├── test_services.py        # Logic and engine validation
│   │   └── test_volume.py          # Stress testing
│   └── templates/
│       └── dashboard/              # HTML layout templates
│
├── frontend/                       # Vite/Svelte frontend assets
│   └── src/
│       ├── main.css                # Tailwind directives and themes
│       ├── main.js                 # Javascript application boundary
│       ├── lib/chartAction.js      # Declarative bindings for Chart.js
│       └── components/
│           ├── ReportBuilder.svelte# Interactive chart builder
│           ├── Navbar.svelte       # Main Navigation UI
│           └── ui/                 # Reusable interface tools
│
├── static/                         # Rendered external statics
├── Dockerfile                      # Application container schema
├── docker-compose.yml              # Cluster definition
├── start.sh                        # Service boot instructions
└── vite.config.js                  # Frontend compilation parameters
```

---

## Infrastructure & Deployment

### Container Lifecycle

The platform operates autonomously through a containerized abstraction built on `python:3.12-slim`:

1. Installs robust required operational system binaries (`curl`, `build-essential`, `libpq-dev`).
2. Configures the ultra-fast JavaScript runtime **Bun** natively over classical Node.js environments.
3. Provisions pure Python distributions based on the local environment map.
4. Uses `start.sh` internally to compile the frontend assets over Vite and load the Python WSGI layer in tandem.

**Ports:** `8000` (Django HTTP Interface) and `5173` (Vite Hot Module Replacement - HMR)

### Local Launch

```bash
sudo docker compose up --build -d
```
All system development features hot-reload on saved changes utilizing volume mounts configured in the compose file.

---

## Continuous Integration (CI)

Integrated Github Actions natively to maintain system integrity continuously over `main` branch cycles.

- **Docker Build Validation** (`docker-build.yml`): Verifies infrastructural definitions cleanly compile out of the `Dockerfile` preventing syntax disruptions in isolated environments.
- **Automated Service Tests** (`django-tests.yml`): Spins up native functional integration replicas over Docker Compose natively testing logical behaviors before dismantling dynamically. 

---

## Application: Dashboard

The application delegates all internal processes under a single Django app domain: `dashboard`.

### Core Models

The domain architecture separates standard configuration objects from immutable parsed analytical records.

- **`User`**: Foundational entity structure allowing extension logic over platform administrators.
- **`TableTemplate` & `TemplateColumn`**: Definitive schemas structuring valid column profiles allowing custom data parsing frameworks defined natively by users.
- **`Dataset`**: The root analytical entity encapsulating uploaded file data linked directly to a previously stored configuration structure.
- **`DatasetImport` & `DatasetCellIssue`**: Audit trail objects detailing previous document ingestion history and parsing anomalies.
- **`DatasetRow`**: Stores the finalized verified dataset variables dynamically encoded into standard JSON objects indexing back natively to their relevant `Dataset`.
- **`Report`**: Configurations designed explicitly representing analytical UI representations linking charts and metric data to an active interface widget.

### Services & Processing

The logic relies on stateless functional components instead of heavy objects models.
- **Import Engine**: Divided logically across Reading (converting files computationally to DataFrames), Mapping (predicting headers iteratively), Validating (enforcing column types securely), and Executing (upserting raw items efficiently scaling data architectures).
- **Query Engine**: `report_query.py` implements a sophisticated extraction pattern using `pandas` natively aggregating stored `DatasetRows`. It seamlessly outputs configured variables preventing dimension leakages dynamically ensuring charts always receive predictable `Chart.js` object arrays stripped of inner variable properties.

### Views & Routing

Endpoints leverage server-side logic rendering with integrated client overlays.

| URL Pattern                    | Description                                  | Auth Needed |
|--------------------------------|----------------------------------------------|-------------|
| `/`                            | The base view and primary application hub.   | Yes         |
| `/login/` / `/register/`       | Standard user entry gates.                   | No          |
| `/formatos/` endpoints         | Complete template modeling suite.            | Yes         |
| `/datasets/` endpoints         | Ingestion interface managing data uploads.   | Yes         |
| `/reportes/<pk>/builder/`      | Comprehensive client analytical environment. | Yes         |

---

## Data Pipeline

The template and execution system is the backbone of the application.

1. **Modeling**: A user provisions custom column structures securely specifying expected configurations (Integers, Decimals, Text, Dates, etc.).
2. **Ingesting**: Valid `.csv` schemas load dynamically mapped heuristically preventing tedious manual configurations.
3. **Execution**: The system executes raw row iterations recording failed data conversions transparently keeping healthy records cleanly processed.

---

## Query Engine & Reporting

The analytical UI heavily relies on native **Svelte 5 Proxies** and declarative component actions orchestrating data flow dynamically. 

The API interacts with `execute_widget()` passing metrics and dimension parameters logically formatting aggregations efficiently utilizing deep Pandas structures. The resulting mathematical output gracefully parses tuples resolving Svelte proxy state wrappers smoothly rendering into modern **Chart.js** visuals natively inside `ReportBuilder.svelte`.

It supports advanced parsing dimensions over Pie, Line, and Bar iterations alongside standard HTML Table derivations seamlessly updating in real-time.

---

## Frontend & Styling

The frontend fundamentally runs an "Islands Architecture" framework natively compiling via Vite pushing `.js` and `.css` artifacts internally tracked through the `django-vite` utility map. 

### Design Identity

The CSS uses **Catppuccin Mocha** natively bound via Tailwind CSS v4 variables over pristine glassmorphism components.

| Token          | Hex       | Element Assignment              |
|----------------|-----------|----------------------------------|
| `cat-base`     | `#1e1e2e` | Main Document Background         |
| `cat-surface0` | `#313244` | Card Boundaries                  |
| `cat-text`     | `#cdd6f4` | Base Element Typography          |
| `cat-mauve`    | `#cba6f7` | Prominent User Actions           |
| `cat-red`      | `#f38ba8` | Destructive Execution Variables  |

Svelte components actively replace static element containers defined in template loops (i.e. `<div id="svelte-report-builder"></div>`) hydrating dynamic functional tools automatically over Page Load.

---

## Authentication Flow

Authentication relies natively on robust Django Session infrastructures.

1. **Gates**: Anonymous sessions natively redirect out of secure analytical scopes seamlessly. 
2. **Registry**: Initialized accounts dynamically log into active session pools without secondary loops.
3. **Sessions**: Data parameters enforce a one-hour timeout structure securely preventing left-over terminals.

---

## Testing Suite

Validating operational features natively executed via an integrated parallel matrix locally and securely across CI nodes.

```bash
# Execute local unit execution mapping
sudo docker compose exec web python manage.py test dashboard.tests
```

**Scope Validation Categories**:
- `test_models.py`: Verifies internal integrity relationships correctly triggering constraints logically preventing structural database failures.
- `test_views.py`: Enforces endpoints return specific UI fragments or HTTP state boundaries consistently validating internal isolation layers over separate user interactions.
- `test_services.py`: Asserts Pandas extraction scripts and Data parsing structures validate or isolate erroneous logic gracefully without crashing server nodes. Tests confirm chart outputs perfectly assemble object parameters uniformly.
- `test_volume.py`: Records runtime statistics executing massive matrix datasets ensuring operational processing scales properly under heavier metric loads safely.

---

*System Updated: April 2026*
