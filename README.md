```text
  ______ ______ ____   ___           _____  _____  
 |  ____|___  /|  _ \ / _ \    /\   |  __ \|  __ \ 
 | |__     / / | |_) | | | |  /  \  | |__) | |  | |
 |  __|   / /  |  _ <| | | | / /\ \ |  _  /| |  | |
 | |     / /__ | |_) | |_| |/ ____ \| | \ \| |__| |
 |_|    /_____||____/ \___//_/    \_\_|  \_\_____/ 
```
---
# FzBoard Web

> A sophisticated web-based data analysis and reporting platform built with **Django 6.0** and **Svelte 5** (via **Vite**). Styled precisely with **Tailwind CSS v4** (Catppuccin Mocha), and containerized for deployment utilizing **Kubernetes**, **Helm**, and **Minikube**.
>
> *The dashboard interface utilizes the Svelte Islands pattern to mount highly dynamic widgets natively within the Django architecture.*

---

## Table of Contents

1. [Architectural Stack](#architectural-stack)
2. [Project Structure](#project-structure)
3. [Infrastructure & Deployment](#infrastructure--deployment)
4. [Continuous Integration (CI)](#continuous-integration-ci)
5. [Application: Dashboard](#application-dashboard)
6. [Data Pipeline](#data-pipeline)
7. [Query Engine & Reporting](#query-engine--reporting)
8. [Frontend & Styling](#frontend--styling)
9. [Documentation](#documentation)

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
| Containerization | Docker Multi-Stage Build      | —       |
| Orchestration    | Kubernetes, Helm, Minikube    | —       |

---

## Infrastructure & Deployment

FzBoard represents a modern production-ready deployment natively built for Kubernetes.

### Local Kubernetes Launch
The platform completely abstracts Docker logic into a unified `Makefile` that orchestrates a local Minikube cluster:
```bash
make up         # Spin up Minikube, build containers, deploy Helm charts
make forward    # Tunnel traffic to localhost:8000
make down       # Teardown the environment completely
```

### Production Mechanics
- **Multi-Stage Dockerfile:** The builder layers `bun` and `node_modules` solely to parse Tailwind CSS and Svelte into static minified assets, permanently stripping dependencies from the final python payload.
- **Static Resolution:** Django natively captures the transpiled javascript bundles and proxies them alongside standard image assets utilizing `WhiteNoise`, eliminating the need for strict front-facing Nginx nodes in small architectures.
- **Helm Persistence:** The default database (`/app/data/db.sqlite3`) maps securely to a Kubernetes `PersistentVolumeClaim` (PVC), protecting mission-critical analysis metrics from stateless container disruptions. 

*(For a deeper dive into the system build process, please read [`docs/architecture-pipeline.md`](docs/architecture-pipeline.md)).*

---

## Continuous Integration (CI)

Integrated Github Actions natively to maintain system integrity continuously over `main` branch cycles.

- **Kubernetes E2E Testing (`k8s-tests.yml`)**: Automates a complete mirror of the production stack. It provisions a temporary Linux-based Minikube cluster, installs the Helm charts seamlessly, verifies Pod readiness wait-states, actively initializes Django Database Migrations, and runs isolated HTTP assertions over port-forwarding to rigidly validate successful styling extraction.

---

## Application: Dashboard

The application delegates all internal processes under a single Django app domain: `dashboard`.

### Core Models
The domain architecture separates standard configuration objects from immutable parsed analytical records.
- **`User`**: Foundational entity structure allowing extension logic over platform administrators.
- **`TableTemplate` & `TemplateColumn`**: Definitive schemas structuring valid column profiles allowing custom data parsing frameworks defined natively by users.
- **`Dataset`**: The root analytical entity encapsulating uploaded file data linked directly to a previously stored configuration structure.
- **`DatasetRow`**: Stores the finalized verified dataset variables dynamically encoded into standard JSON objects indexing back natively to their relevant `Dataset`.
- **`Report`**: Configurations designed explicitly representing analytical UI representations linking charts and metric data to an active interface widget.

### Services & Processing
The logic relies on stateless functional components instead of heavy objects models.
- **Import Engine**: Divided logically across Reading, Mapping, Validating, and Executing bulk row upserts.
- **Query Engine**: `report_query.py` implements a sophisticated extraction pattern using `pandas` natively aggregating stored `DatasetRows`. It seamlessly outputs configured variables dynamically ensuring `Chart.js` object arrays receive predictable isolated variables.

---

## Data Pipeline

1. **Modeling**: A user provisions custom column structures securely specifying expected configurations (Integers, Decimals, Text, Dates, etc.).
2. **Ingesting**: Valid `.csv` schemas load dynamically mapped heuristically preventing tedious manual configurations.
3. **Execution**: The system executes raw row iterations recording failed data conversions transparently keeping healthy records cleanly processed.

---

## Query Engine & Reporting

The analytical UI heavily relies on native **Svelte 5 Proxies** and declarative component actions orchestrating data flow dynamically. 

The API interacts with `execute_widget()` passing metrics and dimension parameters logically formatting aggregations efficiently utilizing deep Pandas structures. The resulting mathematical output gracefully parses tuples resolving Svelte proxy state wrappers smoothly rendering into modern **Chart.js** visuals natively inside `ReportBuilder.svelte`.

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

Svelte components actively replace static element containers defined in template loops (i.e. `<div id="svelte-report-builder"></div>`) hydrating dynamic functional tools automatically over Page Load.

---

## Documentation

For further reading regarding local deployment commands, operations, and architectural breakdowns, reference the inner `docs/` repository files securely:
- [`docs/local-development.md`](docs/local-development.md) - Operating Minikube and managing SQLite Migrations.
- [`docs/architecture-pipeline.md`](docs/architecture-pipeline.md) - Deep dive into Builder states and Deployment infrastructures.

---
*System Updated: April 2026*
