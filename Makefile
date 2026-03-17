.PHONY: install lint format typecheck test test-cov test-integration docker-build docker-up docker-down docker-logs clean help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in editable mode with dev dependencies
	pip install -e ".[dev]"

lint: ## Run ruff linter on source and tests
	ruff check src/ tests/

format: ## Run ruff formatter on source and tests
	ruff format src/ tests/

typecheck: ## Run mypy type checker on source
	mypy src/

test: ## Run unit tests with pytest
	pytest tests/ -v

test-cov: ## Run tests with coverage report
	pytest tests/ --cov=enterprise_mcp --cov-report=html --cov-report=term -v

test-integration: ## Run integration tests
	pytest tests/integration/ -v

docker-build: ## Build Docker image
	docker build -t enterprise-mcp-server:latest .

docker-up: ## Start all services with docker-compose
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Follow docker-compose logs
	docker compose logs -f

clean: ## Remove build artifacts and caches
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
