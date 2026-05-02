.PHONY: install dev test test-unit test-integration lint format clean migrate migrate-create docker-up docker-down docker-build docker-logs

install:
	poetry install

dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest tests/ -v --cov=app --cov-report=term-missing

test-unit:
	poetry run pytest tests/unit/ -v

test-integration:
	poetry run pytest tests/integration/ -v

lint:
	poetry run ruff check app/ tests/

format:
	poetry run ruff format app/ tests/
	poetry run ruff check --fix app/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache test_app.db

migrate:
	poetry run alembic upgrade head

migrate-create:
	poetry run alembic revision --autogenerate -m "$(msg)"

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f
