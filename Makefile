.PHONY: uv manage format format-check lint typecheck pip bash test

uv:
	docker compose exec backend uv $(filter-out $@,$(MAKECMDGOALS))

manage:
	make uv run manage.py $(filter-out $@,$(MAKECMDGOALS))

format:
	make uv run ruff format .

format-check: 
	make uv run ruff format --check .

lint:
	make uv run ruff check .

typecheck:
	make uv run ty check .

pip:
	make uv pip $(filter-out $@,$(MAKECMDGOALS))

bash:
	docker compose exec backend bash	

test:
	make uv run pytest .
