# Stocks Backend

A Django-based backend service for managing stock market data and transactions.

## Features

- Stock price tracking and historical data
- Real-time price updates via SSE
- User authentication with Clerk
- Stock transactions and order management
- RESTful API with Django REST Framework
- OpenAPI documentation with drf-spectacular

## Requirements

- Python 3.13+
- PostgreSQL
- Docker (optional)

## Development Setup

1. Install uv:
```bash
pip install uv
```

2. Install dependencies:
```bash
cd backend
uv pip install ".[dev]"
```

3. Set up environment variables:
```bash
cp .env.example .env  # Create .env file from example
# Edit .env with your configuration
```

4. Run migrations:
```bash
uv run manage.py migrate
```

5. Start the development server:
```bash
uv run manage.py runserver
```

## Running with Docker

First, start the containers:

```bash
docker compose up --build
```

Available commands to run in the container:

```bash
make uv <command>      # Run uv commands in the container
make manage <command>  # Run Django management commands
make format            # Format code with ruff
make lint              # Run ruff linter
make typecheck         # Run mypy type checking
make test              # Run pytest
make bash              # Open a bash shell in the container
make pip <command>     # Run pip commands in the container
make schema-gen        # Regenerate backend/schema.yml OpenAPI spec
```

## Code Quality

- Type checking: `make typecheck`
- Linting: `make lint`
- Formatting: `make format`

## API Documentation

Once the server is running, you can access:
- OpenAPI Schema: http://localhost:8000/api/schema/
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc/ 