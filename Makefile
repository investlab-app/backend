.PHONY: uv pip manage format format-check lint lint-check type-check bash test

uv:
	docker compose exec backend uv $(filter-out $@,$(MAKECMDGOALS))

pip:
	docker compose exec backend uv pip $(filter-out $@,$(MAKECMDGOALS))

manage:
	docker compose exec backend uv run manage.py $(filter-out $@,$(MAKECMDGOALS))

format:
	docker compose exec backend uv run ruff format .

format-check:
	docker compose exec backend uv run ruff format --check .

lint:
	docker compose exec backend uv run ruff check --fix .

lint-check:
	docker compose exec backend uv run ruff check .

type-check:
	docker compose exec backend uv run ty check .

bash:
	docker compose exec backend bash	

test:
	docker compose exec backend uv run pytest . -v

schema-gen:
	docker compose exec backend uv run manage.py spectacular --file schema.yml
