PROJECT_NAME = app
TEST_FOLDER_NAME = tests
TEST_PATH       := ./tests
TEST_WORKERS    := 8

DOCKER_FILENAME := docker-compose.dev.yaml
PYTHON_VERSION = 3.12



PIP      := .venv/bin/pip
UV       := .venv/bin/uv
RUFF     := $(UV) run .venv/bin/ruff
MYPY     := $(UV) run .venv/bin/mypy
PYTEST   := $(UV) run .venv/bin/pytest
ALEMBIC  := $(UV) run $(PYTHON) -m $(PROJECT_NAME).adapters.database
COVERAGE := $(UV) run .venv/bin/coverage

clean_dev: ## Remove virtual environment
	rm -rf .venv

venv: clean_dev ## Create venv
	python$(PYTHON_VERSION) -m venv .venv

develop: venv  ## Create venv, install tools & pre-commit
	$(PIP) install uv
	$(UV) sync
	UV_PROJECT_ENVIRONMENT=.venv $(UV) sync --python $(PYTHON_VERSION) --dev
	$(UV) run pre-commit install

local: ## Start local stack (build & recreate)
	docker compose -f $(DOCKER_FILENAME) up --build --force-recreate --remove-orphans --renew-anon-volumes

local_down: ## Stop local stack and remove volumes
	docker compose -f $(DOCKER_FILENAME) down -v

local-create-migrations:
	$(ALEMBIC) revision --autogenerate

local-apply-migrations:
	$(ALEMBIC) upgrade head

local-delete-migrations:
	find $(PROJECT_NAME)/adapters/database/migrations/versions -type f ! -name '__init__.py' -delete

local-recreate-migrations: local-delete-migrations ## Recreate alembic migrations
	$(ALEMBIC) revision --autogenerate
	$(ALEMBIC) upgrade head

test: ## Run tests with verbose output and auto-parallelism
	$(PYTEST) -vx $(TEST_PATH) -vv -n $(TEST_WORKERS)

test-ci: ## Run tests with coverage and junit report for CI (GitHub Actions)
	$(COVERAGE) erase
	$(COVERAGE) run -m pytest $(TEST_PATH) --junitxml=junit.xml -rs -n $(TEST_WORKERS)
	$(COVERAGE) combine
	$(COVERAGE) report
	$(COVERAGE) xml -o coverage.xml

format: ## Format code with ruff
	$(RUFF) format .
	$(RUFF) check --fix .

ruff: ## Run ruff linter only
	$(RUFF) check ./$(PROJECT_NAME)

mypy: ## Run mypy type checker
	$(MYPY) ./$(PROJECT_NAME)

lint: format mypy ## Full lint cycle (format + mypy) - local use only

lint-ci: ## Run linters in CI without formatting
	@$(MAKE) ruff
	@$(MAKE) mypy


app: ## Start uvicorn in reload mode
	$(UV) run python -m $(PROJECT_NAME)


help: ## Show this help
	@echo "Available commands:"
	@grep -E "^[a-zA-Z_-]+:.*##" $(MAKEFILE_LIST) | sed "s/:.*##/ /"
