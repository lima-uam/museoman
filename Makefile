.PHONY: install dev test lint fmt migrate shell seed

install:
	uv sync --all-groups

dev:
	uv run python manage.py runserver

test:
	uv run pytest

test-fast:
	uv run pytest -q --no-cov

lint:
	uv run ruff check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

migrate:
	uv run python manage.py makemigrations
	uv run python manage.py migrate

shell:
	uv run python manage.py shell

seed:
	uv run python manage.py seed_demo

createadmin:
	uv run python manage.py createadmin

db-up:
	docker compose up -d

db-down:
	docker compose down
