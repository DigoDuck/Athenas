DEV = docker compose -f docker-compose.dev.yml

.PHONY: lint test dev-up dev-down use-init use-up use-down

lint:
	$(DEV) run --rm --no-deps backend sh -c "ruff check . && ruff format --check ."
	$(DEV) run --rm --no-deps frontend npm run lint

test:
	$(DEV) run --rm backend pytest

dev-up:
	$(DEV) up -d --build

dev-down:
	$(DEV) down

use-init:
	python scripts/use.py init

use-up:
	python scripts/use.py up

use-down:
	python scripts/use.py down
