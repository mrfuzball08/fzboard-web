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
4. Instructs Helm to install/upgrade the server deployment (`make deploy`) and safely bypasses validation webhook timeouts.

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
When you run `make down`, the PVC is often destroyed depending on Minikube's garbage collection loop. The very next time you run `make up`, an entirely fresh empty hard drive mounts.
Because Django dynamically establishes the database file `db.sqlite3` upon attempting to serve a webpage, it will silently crash `(Server Error 500)` during authentication because the database has absolutely zero tables in it.

### When to Run Migrations
You must **manually run migrations** using `make migrate` in the following scenarios:
1. Immediately after calling `make up` following a `make down` purge.
2. Right after pulling fresh codebase changes containing new Django app migrations.
3. Whenever a `500 Server Error` traceback reveals a `sqlite3.OperationalError: no such table`.

**How to repair the database:**
1. Let the pod finish booting up `make up`.
2. Apply all schema updates inside the running pod:
```bash
make migrate
```
3. Because the entire database resets, you will usually need to quickly forge a fresh superuser through the shell so you can actually log in:
```bash
make shell
# Inside the container:
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
```
