.PHONY: help install dev test lint format docker-up docker-down init-db clean run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

dev: ## Install dependencies including dev
	poetry install --with dev

test: ## Run tests with coverage
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

test-unit: ## Run only unit tests
	poetry run pytest tests/unit/

test-integration: ## Run only integration tests
	poetry run pytest tests/integration/

lint: ## Run linters (ruff + mypy)
	poetry run ruff check src tests
	poetry run mypy src

format: ## Format code with black
	poetry run black src tests

format-check: ## Check code formatting without changing
	poetry run black --check src tests

quality: format lint ## Run all code quality checks

docker-up: ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-clean: ## Stop and remove all containers and volumes (WARNING: deletes data)
	docker-compose down -v
	rm -rf qdrant_storage neo4j_data neo4j_logs postgres_data

init-db: ## Initialize all databases
	poetry run python scripts/init_db.py

run: ## Run the application
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run in production mode
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

shell: ## Open poetry shell
	poetry shell

clean: ## Clean cache and temporary files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

setup: install docker-up init-db ## Full setup: install + docker + init DB
	@echo "Setup complete! Run 'make run' to start the application"

# Workflow shortcuts
dev-start: docker-up run ## Start Docker services and run app

dev-stop: docker-down ## Stop all development services

rebuild: docker-down docker-up init-db ## Rebuild all services

# Documentation
docs: ## Generate documentation (if applicable)
	@echo "API docs available at http://localhost:8000/docs when running"

# Database management
db-shell-postgres: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U aion_user -d aion_metadata

db-shell-neo4j: ## Open Neo4j browser
	@echo "Opening Neo4j Browser at http://localhost:7474"
	open http://localhost:7474 || xdg-open http://localhost:7474 2>/dev/null || true

# Default target
.DEFAULT_GOAL := help
