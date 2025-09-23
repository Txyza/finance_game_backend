# Finance Game API Makefile

.PHONY: help build run stop

# Colors for output
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m

# Profile selection (dev or prod)
PROFILE ?= dev

# Compose file selection based on profile
ifeq ($(PROFILE),prod)
	COMPOSE_FILE = docker-compose.prod.yml
	ENV_FILE = .env.prod
else
	COMPOSE_FILE = docker-compose.yml
	ENV_FILE = .env
endif

help: ## Show help
	@echo "$(GREEN)Finance Game API$(NC)"
	@echo "=================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Usage with profiles:"
	@echo "  $(YELLOW)make build PROFILE=dev$(NC)   - Build development images"
	@echo "  $(YELLOW)make run PROFILE=prod$(NC)    - Run production environment"
	@echo "  $(YELLOW)make stop$(NC)                 - Stop current environment"

# Build Commands
build: ## Build Docker images (use PROFILE=dev|prod)
	@echo "$(GREEN)Building $(PROFILE) Docker images...$(NC)"
	@if [ "$(PROFILE)" = "prod" ]; then \
		docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) build; \
	else \
		docker-compose -f $(COMPOSE_FILE) build; \
	fi

# Run Commands
run: ## Run environment (use PROFILE=dev|prod)
	@echo "$(GREEN)Starting $(PROFILE) environment...$(NC)"
	@if [ "$(PROFILE)" = "prod" ]; then \
		docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up --build -d; \
	else \
		docker-compose -f $(COMPOSE_FILE) up --build -d; \
	fi

# Stop Commands
stop: ## Stop containers
	@echo "$(YELLOW)Stopping containers...$(NC)"
	@if [ -f docker-compose.prod.yml ] && [ "$(shell docker-compose -f docker-compose.prod.yml ps -q)" ]; then \
		docker-compose -f docker-compose.prod.yml down; \
	fi
	@if [ -f docker-compose.yml ] && [ "$(shell docker-compose ps -q)" ]; then \
		docker-compose down; \
	fi

# Database Commands
migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	docker-compose exec api alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MESSAGE="description")
	@echo "$(GREEN)Creating new migration...$(NC)"
	docker-compose exec api alembic revision --autogenerate -m "$(MESSAGE)"

migrate-downgrade: ## Downgrade migration by one
	@echo "$(YELLOW)Downgrading migration...$(NC)"
	docker-compose exec api alembic downgrade -1

# Utility Commands
logs: ## Show logs (usage: make logs SERVICE=api)
	@if [ -z "$(SERVICE)" ]; then \
		docker-compose logs -f; \
	else \
		docker-compose logs -f $(SERVICE); \
	fi

logs-prod: ## Show production logs
	@if [ -z "$(SERVICE)" ]; then \
		docker-compose -f docker-compose.prod.yml logs -f; \
	else \
		docker-compose -f docker-compose.prod.yml logs -f $(SERVICE); \
	fi

shell: ## Get shell access to API container
	@echo "$(BLUE)Opening shell in API container...$(NC)"
	docker-compose exec api /bin/bash

shell-prod: ## Get shell access to production API container
	@echo "$(BLUE)Opening shell in production API container...$(NC)"
	docker-compose -f docker-compose.prod.yml exec api /bin/bash

# Testing Commands
test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	docker-compose exec api python -m pytest

test-cov: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	docker-compose exec api python -m pytest --cov=app --cov-report=html

# Cleanup Commands
clean: ## Clean up containers and volumes
	@echo "$(YELLOW)Cleaning up containers and volumes...$(NC)"
	docker-compose down -v
	docker system prune -f

clean-all: ## Clean up everything (containers, volumes, images)
	@echo "$(YELLOW)Cleaning up everything...$(NC)"
	docker-compose down -v --rmi all
	docker system prune -af

# Health check
health: ## Check API health
	@echo "$(GREEN)Checking API health...$(NC)"
	@curl -s http://localhost:8000/api/v1/health | jq . || echo "Health check failed"

# Environment setup
env: ## Copy environment files
	@echo "$(GREEN)Setting up environment files...$(NC)"
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi
	@if [ ! -f .env.prod ]; then echo "Using existing .env.prod"; fi

.DEFAULT_GOAL := help