.PHONY: manage format pip bash test lint typecheck

manage:
	docker compose exec backend python3 manage.py $(filter-out $@,$(MAKECMDGOALS))

format:
	docker compose exec backend isort .
	docker compose exec backend black .

lint:
	docker compose exec backend pylint .

typecheck:
	docker compose exec backend mypy .

pip:
	docker-compose exec backend pip3 $(filter-out $@,$(MAKECMDGOALS))

bash:
	docker compose exec backend bash

test:
	docker compose exec backend pytest .
