# Makefile

# Variables
PYTHON = python3

# Environment
ENV = .env
PORT = 8000

# Source setup
.PHONY: setup
setup:
	python -m venv .venv
	source .venv/bin/activate
	pip install -r requirements.txt

# Run fastapi
.PHONY: run
run:
	python -m uvicorn main:app --reload --env-file $(ENV) --host 0.0.0.0 --port $(PORT)

# Alembic
.PHONY: init_migration
init_migration:
	alembic init --template async src/infrastructure/persistence/migrations

.PHONY: add-migration
add_migration:
	alembic revision --autogenerate -m "$(MIGRATION)"

.PHONY: migrate
migrate:
	alembic upgrade head

.PHONY: alembic-downgrade
alembic-downgrade:
	alembic downgrade -1

.PHONY: alembic-stamp
alembic-stamp:
	alembic stamp head

.PHONY: alembic-history
	alembic history

.PHONY: alembic-current
alembic-current:
	alembic current


# Initialize Alembic migrations
.PHONY: celery-flower
celery-flower:
	celery -A src.core.utilities.celery.celery_app flower --port=5555

.PHONY: celery-worker
celery-worker:
	celery -A src.core.utilities.celery.celery_app worker --loglevel=info

.PHONY: run-notification-worker
run-notification-worker:
	$(PYTHON) -m src.application.workers.notification_sender

# Run the tests
.PHONY: test
test:
	$(PYTHON) -m pytest tests/

.PHONY: clean-cache
clean-cache:
	rm -rf __pycache__ *.pyc .pytest_cache

.PHONY: clean-env
clean-env:
	rm -rf $(ENV)

.PHONY: clean-venv
clean-venv:
	rm -rf .venv

.PHONY: clean
clean:
	make clean-cache
	make clean-env
	make clean-venv

.PHONY: install-dependencies
install-dependencies:
	pip install -t dependencies -r requirements.txt  --platform manylinux2014_x86_64 --only-binary=:all:


.PHONY: zip-dependencies
zip-dependencies:
	cd dependencies; zip ../lambda_artifact.zip -r .

.PHONY: zip-app
zip-app:
	zip -g lambda_artifact.zip -r . -x '*.git*' '*.github*' '__pycache__*' '*venv*' 'farm_methane.*' 'makefile' 'vercel.json' '.vercelignore' 'dependencies*'

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  setup        Setup the environment"
	@echo "  run          Run the FastAPI application"
	@echo "  alembic-init        Initialize the Alembic migrations"
	@echo "  alembic-revision    Create a new migration"
	@echo "  alembic-upgrade     Upgrade the migrations"
	@echo "  alembic-downgrade   Downgrade the migrations"
	@echo "  alembic-stamp       Stamp the migrations"
	@echo "  alembic-history     Show the migration history"
	@echo "  alembic-current     Show the current migration"
	@echo "  test               Run the tests"
	@echo "  clean              Clean the environment"
	@echo "  clean-cache        Clean the cache"
	@echo "  clean-env          Clean the environment"
	@echo "  clean-venv         Clean the venv"
