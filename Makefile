.PHONY: manage format format-check lint typecheck pip bash test install-dev

manage:
	docker compose exec backend python3 manage.py $(filter-out $@,$(MAKECMDGOALS))

format:
	docker compose exec backend ruff format .

format-check: 
	docker compose exec backend ruff format --check .

lint:
	docker compose exec backend ruff check .

typecheck:
	docker compose exec backend mypy .

pip:
	docker compose exec backend uv pip $(filter-out $@,$(MAKECMDGOALS))

install-dev:
	docker compose exec backend uv pip install -e ".[dev]"

bash:
	docker compose exec backend bash

test:
	docker compose exec backend pytest .
