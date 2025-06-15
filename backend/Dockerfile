FROM python:3.13-slim-bookworm

RUN apt-get update \
  && apt-get install -y netcat-traditional \
  && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
  && apt-get clean \
  && mkdir /backend

# Set the working directory inside the container
WORKDIR /backend

# Set environment variables
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (todo seperate dev and prod image)
RUN uv sync --locked --no-dev 

# Copy the rest of the project files
COPY . /backend/

# Add permissions to the entrypoint script
RUN chmod +x /backend/entrypoint.sh

# Expose the Django port
EXPOSE 8000

# Run Django's development server
ENTRYPOINT ["/bin/bash", "/backend/entrypoint.sh"]
