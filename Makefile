.PHONY: install dev test test-unit test-integration lint format typecheck check clean migrate migrate-create docker-up docker-down docker-build docker-logs

install:
	uv sync

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest -v --cov=app --cov-report=term-missing

test-unit:
	uv run pytest tests/unit -v

test-integration:
	uv run pytest tests/integration -v

lint:
	uv run ruff check app tests
	uv run ruff format --check app tests

format:
	uv run ruff format app tests
	uv run ruff check --fix app tests

typecheck:
	uv run mypy

# Everything CI runs. Use before opening a pull request.
check: lint typecheck test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache .mypy_cache test_app.db

migrate:
	uv run alembic upgrade head

migrate-create:
	uv run alembic revision --autogenerate -m "$(msg)"

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build

docker-logs:
	docker compose logs -f
