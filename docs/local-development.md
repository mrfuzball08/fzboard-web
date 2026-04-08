# Developing FzBoard Locally

This document outlines the standard workflows to boot up, interact with, and tear down FzBoard locally using Minikube and Kubernetes. In our system, the `Makefile` isolates and automates the verbose command-line operations of Docker, Helm, and Kubectl.

## Managing the Service

The entire FzBoard application runs inside a local Kubernetes cluster (Minikube).

### 1. Turning On the Service (`make up`)
To boot the application from a cold state, run:
```bash
make up
```
**What this does behind the scenes:**
1. Starts the Minikube cluster and configures your Docker daemon.
2. Builds the latest `fzboard-web:latest` container natively using the `Dockerfile`.
3. Loads the newly compiled image directly into Minikube's local cache.
4. Instructs Helm to install or upgrade the server deployment (`make deploy`) and safely bypasses validation webhook timeouts.

If Minikube is already running and you only changed application code, `make deploy` is usually enough.

### 2. Accessing the Application (`make forward`)
Because the application runs natively inside the Minikube virtual network, it does not touch your laptop's standard `8000` port automatically. To access the interface, run:
```bash
make forward
```
This will "hang" your terminal, creating an active tunnel from the pod to `http://localhost:8000`. You can press `Ctrl + C` at any time to stop forwarding.

### 3. Turning Off the Service (`make down`)
If you want to free up laptop resources or completely reset your testing environment, run:
```bash
make down
```
**Important:** Running `make down` will completely destroy the Helm release, delete all pods, heavily purge local persistent volumes attached to the isolated test network, and shut off Minikube securely to save RAM. 

---

## Database State and Migrations

FzBoard uses a local SQLite database that is mounted to the Kubernetes Pod via a `PersistentVolumeClaim` (PVC). This behaves like a persistent hard drive. However, **how you manage your cluster significantly affects the database.**

### The "Empty Database" Trap
When you run `make down`, the PVC may be recreated or detached depending on how Minikube tears down the environment. The next `make up` can therefore attach a completely fresh empty volume.
To prevent the old `Server Error (500)` login failure on a blank SQLite volume, startup now follows this flow automatically:
1. Helm mounts the PVC at `/app/data`.
2. An init container creates `/app/data/db` and `/app/data/media` with the right ownership.
3. The Django container runs `python manage.py migrate --noinput`.
4. Gunicorn starts only after the schema is present.

### When to Run Migrations
Most of the time you do not need to run migrations manually because pod startup now applies them automatically.
Use `make migrate` in the following scenarios:
1. You want to re-apply schema changes in an already running pod without redeploying.
2. You pulled new migrations into a pod that is already running.
3. You are recovering from a failed startup and need to retry migrations directly.

**How to repair the database:**
1. Let the pod finish booting up `make up`.
2. If startup failed before migrations completed, apply schema updates inside the running pod:
```bash
make migrate
```
3. If the database is brand new, create a user so you can log in:
```bash
make shell
# Inside the container:
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
```
