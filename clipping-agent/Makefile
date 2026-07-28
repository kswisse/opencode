.PHONY: infra up down build test lint

infra:
	docker compose -f docker-compose.infra.yml up -d

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

test:
	cd apps/api && pytest
	cd apps/worker && pytest

lint:
	ruff check apps/ packages/
	mypy apps/ packages/
