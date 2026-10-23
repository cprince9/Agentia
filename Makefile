# ==============================================================================
# MASDS (Multi-Agent Software Development System) Developer Makefile
# ==============================================================================

SHELL := /bin/bash
COMPOSE := docker compose

.DEFAULT_GOAL := help
.PHONY: help dev build down logs migrate seed-rag backend-shell test clean

help: ## Show this help message
	@echo "================================================================================"
	@echo "MASDS (Multi-Agent Software Development System) - Control Center"
	@echo "================================================================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "================================================================================"

dev: ## Start all services in development mode
	@echo "Starting MASDS services in background..."
	$(COMPOSE) up -d
	@echo "All services started. UI available at http://localhost:3000, API at http://localhost:8000"

build: ## Build all Docker images
	@echo "Building all container images..."
	$(COMPOSE) build --pull

down: ## Stop all services
	@echo "Stopping all MASDS services..."
	$(COMPOSE) down

logs: ## Tail all logs
	$(COMPOSE) logs -f

migrate: ## Run database migrations
	@echo "Applying Alembic database migrations..."
	$(COMPOSE) exec backend alembic -c db/migrations/alembic.ini upgrade head

seed-rag: ## Seed the ChromaDB knowledge base
	@echo "Seeding ChromaDB vector knowledge base..."
	$(COMPOSE) exec backend python -m rag.seed

backend-shell: ## Shell into backend container
	$(COMPOSE) exec backend /bin/bash

test: ## Run all tests
	@echo "Running backend test suite with Pytest..."
	$(COMPOSE) exec backend pytest backend/tests/ -v --cov=backend --cov-report=term-missing

clean: ## Remove all volumes and containers
	@echo "Removing all containers, networks, and persistent data volumes..."
	$(COMPOSE) down -v --remove-orphans
