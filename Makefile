# ============================================
# FzBoard - Makefile
# Kubernetes local deployment with Helm + Minikube
# ============================================

DOCKER_USER ?= mrfuzball
IMAGE_NAME  ?= fzboard-web
TAG         ?= latest
RELEASE     ?= fzboard
NAMESPACE   ?= default

# ── Docker ─────────────────────────────────
.PHONY: build push

build:
	docker build --no-cache -t $(DOCKER_USER)/$(IMAGE_NAME):$(TAG) .

push: build
	docker push $(DOCKER_USER)/$(IMAGE_NAME):$(TAG)

# ── Minikube ───────────────────────────────
.PHONY: minikube-start minikube-stop minikube-load

minikube-start:
	minikube start --driver=docker
	minikube addons enable ingress

minikube-stop:
	minikube stop

minikube-delete:
	minikube delete

minikube-load: build
	minikube image load $(DOCKER_USER)/$(IMAGE_NAME):$(TAG)

purge: down
	@echo "Removing image from Minikube..."
	minikube image rm $(DOCKER_USER)/$(IMAGE_NAME):$(TAG) || true
	@echo "Pruning Docker build cache and images..."
	docker builder prune -af
	docker image prune -af

# ── Helm ───────────────────────────────────
.PHONY: deploy undeploy lint template

deploy: minikube-load
	kubectl delete validatingwebhookconfiguration ingress-nginx-admission --ignore-not-found || true
	helm upgrade --install $(RELEASE) ./helm/fzboard \
		--namespace $(NAMESPACE) \
		--set image.repository=$(DOCKER_USER)/$(IMAGE_NAME) \
		--set image.tag=$(TAG) \
		--wait

undeploy:
	helm uninstall $(RELEASE) --namespace $(NAMESPACE)

lint:
	helm lint ./helm/fzboard

template:
	helm template $(RELEASE) ./helm/fzboard

# ── Kubernetes helpers ─────────────────────
.PHONY: status logs shell migrate forward

status:
	kubectl get pods,svc,ingress -n $(NAMESPACE)

logs:
	kubectl logs -f deployment/$(RELEASE) -n $(NAMESPACE)

shell:
	kubectl exec -it deployment/$(RELEASE) -n $(NAMESPACE) -- /bin/bash

migrate:
	kubectl exec deployment/$(RELEASE) -n $(NAMESPACE) -- python manage.py migrate

forward:
	@echo "Forwarding fzboard port 8000 to localhost:8000..."
	kubectl port-forward svc/$(RELEASE) -n $(NAMESPACE) 8000:8000 --address 0.0.0.0

# ── Full workflow ──────────────────────────
.PHONY: up down hosts

up: minikube-start deploy hosts
	@echo ""
	@echo "✅ FzBoard deployed! Access at http://fzboard.local"

down: undeploy minikube-stop

hosts:
	@echo ""
	@echo "📌 Add this to /etc/hosts if not already present:"
	@echo "  $$(minikube ip) fzboard.local"

# ── Help ───────────────────────────────────
.PHONY: help

help:
	@echo "FzBoard Kubernetes Deployment"
	@echo "=============================="
	@echo ""
	@echo "  make up           - Start Minikube + deploy everything"
	@echo "  make down         - Undeploy + stop Minikube"
	@echo "  make build        - Build Docker image"
	@echo "  make push         - Build + push to Docker Hub"
	@echo "  make deploy       - Build, load into Minikube, helm install"
	@echo "  make undeploy     - Helm uninstall"
	@echo "  make status       - Show pods, services, ingress"
	@echo "  make logs         - Tail pod logs"
	@echo "  make shell        - Open shell in running pod"
	@echo "  make migrate      - Run Django migrations in pod"
	@echo "  make forward      - Forward Kubernetes port 8000 to localhost:8000"
	@echo "  make lint         - Lint the Helm chart"
	@echo "  make template     - Render Helm templates (dry-run)"
	@echo "  make help         - Show this help"
