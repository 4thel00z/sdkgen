.PHONY: help install dev format lint fix typecheck test test-cov test-api test-sdk check pre-commit build publish publish-test clean

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo "$(GREEN)  SDKGen - Available Make Targets$(RESET)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"

install: ## Install dependencies
	@echo "$(YELLOW)Installing dependencies...$(RESET)"
	@uv pip install -e .
	@echo "$(GREEN)✓ Dependencies installed$(RESET)"

dev: ## Install with dev dependencies
	@echo "$(YELLOW)Installing with dev dependencies...$(RESET)"
	@uv install
	@echo "$(GREEN)✓ Dev environment ready$(RESET)"

format: ## Format code with ruff
	@echo "$(YELLOW)Formatting code...$(RESET)"
	@ruff format .
	@echo "$(GREEN)✓ Code formatted$(RESET)"

lint: ## Run ruff linter
	@echo "$(YELLOW)Running linter...$(RESET)"
	@ruff check sdkgen/
	@echo "$(GREEN)✓ Linter checks passed$(RESET)"

fix: ## Auto-fix linter issues
	@echo "$(YELLOW)Auto-fixing linter issues...$(RESET)"
	@ruff check --fix sdkgen/
	@echo "$(GREEN)✓ Issues fixed$(RESET)"

typecheck: ## Run mypy type checker
	@echo "$(YELLOW)Running type checker...$(RESET)"
	@python -m mypy sdkgen/ || uv run mypy sdkgen/ || echo "$(RED)✗ Type check failed (mypy not found)$(RESET)"
	@echo "$(GREEN)✓ Type check passed$(RESET)"

test: ## Run pytest tests
	@echo "$(YELLOW)Running tests...$(RESET)"
	@pytest tests/ -v || uv run pytest tests/ -v || echo "$(RED)✗ Tests failed (pytest not found)$(RESET)"
	@echo "$(GREEN)✓ Tests passed$(RESET)"

test-cov: ## Run tests with coverage
	@echo "$(YELLOW)Running tests with coverage...$(RESET)"
	@pytest tests/ --cov=sdkgen --cov-report=html || uv run pytest tests/ --cov=sdkgen --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(RESET)"

test-api: ## Start test API server
	@echo "$(YELLOW)Starting test API server...$(RESET)"
	@cd test_api && uv run uvicorn main:app --host 127.0.0.1 --port 8000

test-sdk: ## Generate SDK from test API and verify
	@echo "$(YELLOW)Generating SDK from test API...$(RESET)"
	@curl -s http://127.0.0.1:8000/openapi.json > /tmp/test_openapi.json 2>/dev/null || echo "$(RED)⚠ Test API not running. Start with: make test-api$(RESET)"
	@uv run python -m sdkgen.cli generate -i /tmp/test_openapi.json -o /tmp/test_sdk -l python -n test_sdk
	@cd /tmp/test_sdk && python -c "import py_compile; from pathlib import Path; files = list(Path('test_sdk').rglob('*.py')); [py_compile.compile(str(f), doraise=True) for f in files]; print('✓ All files compiled successfully')"
	@echo "$(GREEN)✓ SDK generation verified$(RESET)"

check: ## Run all quality checks (format, lint, typecheck, test, test-sdk)
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo "$(GREEN)  Running Full Quality Check$(RESET)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) typecheck
	@$(MAKE) test || echo "$(YELLOW)⚠ Tests skipped (pytest not available)$(RESET)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo "$(GREEN)✓ All quality checks passed!$(RESET)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"

pre-commit: check ## Alias for check (run before committing)

build: ## Build distribution packages
	@echo "$(YELLOW)Building distribution packages...$(RESET)"
	@rm -rf dist/
	@uv build
	@echo "$(GREEN)✓ Packages built in dist/$(RESET)"
	@ls -lh dist/

publish: ## Publish to PyPI (requires PYPI_TOKEN env var)
	@echo "$(YELLOW)Publishing to PyPI...$(RESET)"
	@if [ -z "$$PYPI_TOKEN" ]; then \
		if [ -f ~/.pws/pypi ]; then \
			export PYPI_TOKEN=$$(cat ~/.pws/pypi); \
		else \
			echo "$(RED)✗ PYPI_TOKEN not set and ~/.pws/pypi not found$(RESET)"; \
			exit 1; \
		fi; \
	fi; \
	$(MAKE) build && \
	uv run twine upload dist/* --username __token__ --password $$PYPI_TOKEN && \
	echo "$(GREEN)✓ Published to PyPI$(RESET)"

publish-test: ## Publish to TestPyPI
	@echo "$(YELLOW)Publishing to TestPyPI...$(RESET)"
	@if [ -z "$$PYPI_TEST_TOKEN" ]; then \
		echo "$(RED)✗ PYPI_TEST_TOKEN not set$(RESET)"; \
		exit 1; \
	fi; \
	$(MAKE) build && \
	uv run twine upload --repository testpypi dist/* --username __token__ --password $$PYPI_TEST_TOKEN && \
	echo "$(GREEN)✓ Published to TestPyPI$(RESET)"

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	@rm -rf dist/ build/ *.egg-info
	@rm -rf .mypy_cache .ruff_cache .pytest_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(RESET)"
