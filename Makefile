.PHONY: uv manage format format-check lint typecheck pip bash test

uv:
	docker compose exec backend uv $(filter-out $@,$(MAKECMDGOALS))

manage:
	docker compose exec backend uv run manage.py $(filter-out $@,$(MAKECMDGOALS))

format:
	docker compose exec backend uv run ruff format .

format-check: 
	docker compose exec backend uv run ruff format --check .

lint:
	docker compose exec backend uv run ruff check .

lintfix:
	docker compose exec backend uv run ruff check --fix .

typecheck:
	docker compose exec backend uv run ty check .

pip:
	docker compose exec backend uv pip $(filter-out $@,$(MAKECMDGOALS))

bash:
	docker compose exec backend bash	

test:
	docker compose exec backend uv run pytest .
