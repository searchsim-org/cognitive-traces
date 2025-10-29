.PHONY: help install install-backend install-frontend setup start start-backend start-frontend stop clean test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend build docker-up docker-down docker-logs migrate

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(BLUE)Cognitive Traces - Makefile Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

install: install-backend install-frontend ## Install all dependencies (backend + frontend)
	@echo "$(GREEN)✓ All dependencies installed successfully$(NC)"

install-backend: ## Install backend dependencies with Poetry
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@cd backend && poetry install
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## Install frontend dependencies with pnpm
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@cd frontend && pnpm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

setup: ## Setup environment files
	@echo "$(BLUE)Setting up environment files...$(NC)"
	@if [ ! -f backend/.env ]; then \
		cp backend/env.example backend/.env; \
		echo "$(YELLOW)⚠ Created backend/.env from env.example$(NC)"; \
		echo "$(YELLOW)⚠ Please edit backend/.env with your API keys!$(NC)"; \
	else \
		echo "$(GREEN)✓ backend/.env already exists$(NC)"; \
	fi
	@if [ ! -f frontend/.env.local ]; then \
		cp frontend/env.local.example frontend/.env.local; \
		echo "$(GREEN)✓ Created frontend/.env.local$(NC)"; \
	else \
		echo "$(GREEN)✓ frontend/.env.local already exists$(NC)"; \
	fi

##@ Development

start: ## Start both backend and frontend servers
	@./start.sh

start-backend: ## Start only backend server
	@echo "$(BLUE)Starting backend server...$(NC)"
	@cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start-frontend: ## Start only frontend server
	@echo "$(BLUE)Starting frontend server...$(NC)"
	@cd frontend && pnpm dev

stop: ## Stop all running servers
	@./stop.sh

##@ Testing

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests with pytest
	@echo "$(BLUE)Running backend tests...$(NC)"
	@cd backend && poetry run pytest -v

test-backend-cov: ## Run backend tests with coverage
	@echo "$(BLUE)Running backend tests with coverage...$(NC)"
	@cd backend && poetry run pytest --cov=app --cov-report=html --cov-report=term

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd frontend && pnpm test

##@ Code Quality

lint: lint-backend lint-frontend ## Run linters for both backend and frontend

lint-backend: ## Run backend linters (flake8)
	@echo "$(BLUE)Running backend linters...$(NC)"
	@cd backend && poetry run flake8 app/

lint-frontend: ## Run frontend linters (ESLint)
	@echo "$(BLUE)Running frontend linters...$(NC)"
	@cd frontend && pnpm lint

format: format-backend format-frontend ## Format code for both backend and frontend

format-backend: ## Format backend code with Black and isort
	@echo "$(BLUE)Formatting backend code...$(NC)"
	@cd backend && poetry run black app/
	@cd backend && poetry run isort app/
	@echo "$(GREEN)✓ Backend code formatted$(NC)"

format-frontend: ## Format frontend code with Prettier (if configured)
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	@cd frontend && pnpm format || echo "$(YELLOW)⚠ Prettier not configured$(NC)"

type-check: ## Run type checking
	@echo "$(BLUE)Type checking backend...$(NC)"
	@cd backend && poetry run mypy app/ || echo "$(YELLOW)⚠ mypy not fully configured$(NC)"
	@echo "$(BLUE)Type checking frontend...$(NC)"
	@cd frontend && pnpm type-check

##@ Database

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@cd backend && poetry run alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed$(NC)"

migrate-create: ## Create a new migration (use name=your_migration_name)
	@echo "$(BLUE)Creating new migration: $(name)$(NC)"
	@cd backend && poetry run alembic revision --autogenerate -m "$(name)"

migrate-down: ## Rollback last migration
	@echo "$(BLUE)Rolling back last migration...$(NC)"
	@cd backend && poetry run alembic downgrade -1

##@ Docker

docker-up: ## Start all services with Docker Compose
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Docker services started$(NC)"
	@echo "$(BLUE)Backend: http://localhost:8000$(NC)"
	@echo "$(BLUE)Frontend: http://localhost:3000$(NC)"

docker-down: ## Stop all Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Docker services stopped$(NC)"

docker-logs: ## View Docker logs
	@docker-compose logs -f

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build

docker-clean: ## Remove Docker containers, volumes, and images
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	@docker-compose down -v --rmi all
	@echo "$(GREEN)✓ Docker cleanup complete$(NC)"

##@ Build

build: build-backend build-frontend ## Build both backend and frontend for production

build-backend: ## Build backend (prepare for deployment)
	@echo "$(BLUE)Building backend...$(NC)"
	@cd backend && poetry build
	@echo "$(GREEN)✓ Backend built$(NC)"

build-frontend: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(NC)"
	@cd frontend && pnpm build
	@echo "$(GREEN)✓ Frontend built$(NC)"

##@ Cleanup

clean: clean-backend clean-frontend ## Clean all build artifacts and caches

clean-backend: ## Clean backend artifacts
	@echo "$(BLUE)Cleaning backend...$(NC)"
	@cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@cd backend && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@cd backend && rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
	@echo "$(GREEN)✓ Backend cleaned$(NC)"

clean-frontend: ## Clean frontend artifacts
	@echo "$(BLUE)Cleaning frontend...$(NC)"
	@cd frontend && rm -rf .next out node_modules/.cache
	@echo "$(GREEN)✓ Frontend cleaned$(NC)"

clean-all: clean ## Deep clean including dependencies
	@echo "$(BLUE)Deep cleaning...$(NC)"
	@cd backend && rm -rf .venv
	@cd frontend && rm -rf node_modules
	@echo "$(GREEN)✓ Deep clean complete (run 'make install' to reinstall)$(NC)"

##@ Utilities

check: lint type-check test ## Run all checks (lint, type-check, test)
	@echo "$(GREEN)✓ All checks passed!$(NC)"

dev-setup: setup install migrate ## Complete development setup
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo "$(BLUE)Run 'make start' to begin development$(NC)"

health: ## Check if services are running
	@echo "$(BLUE)Checking services...$(NC)"
	@curl -s http://localhost:8000/health > /dev/null && echo "$(GREEN)✓ Backend is running$(NC)" || echo "$(YELLOW)✗ Backend is not running$(NC)"
	@curl -s http://localhost:3000 > /dev/null && echo "$(GREEN)✓ Frontend is running$(NC)" || echo "$(YELLOW)✗ Frontend is not running$(NC)"

info: ## Show project information
	@echo "$(BLUE)Project: Cognitive Traces$(NC)"
	@echo ""
	@echo "Python version: $$(python3 --version 2>/dev/null || echo 'Not installed')"
	@echo "Poetry version: $$(poetry --version 2>/dev/null || echo 'Not installed')"
	@echo "Node version: $$(node --version 2>/dev/null || echo 'Not installed')"
	@echo "pnpm version: $$(pnpm --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "Backend dependencies installed: $$([ -d backend/.venv ] && echo 'Yes' || echo 'No')"
	@echo "Frontend dependencies installed: $$([ -d frontend/node_modules ] && echo 'Yes' || echo 'No')"

update: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@cd backend && poetry update
	@cd frontend && pnpm update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

# Documentation
docs: ## Open documentation in browser
	@echo "$(BLUE)Opening documentation...$(NC)"
	@open README.md || xdg-open README.md || start README.md

