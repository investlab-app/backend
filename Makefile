.PHONY: manage format format-check lint typecheck pip bash test

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
	docker compose exec backend pip3 $(filter-out $@,$(MAKECMDGOALS))

bash:
	docker compose exec backend bash

test:
	docker compose exec backend pytest .
