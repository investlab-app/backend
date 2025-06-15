FROM ghcr.io/astral-sh/uv:python3.13-bookworm

RUN apt-get update \
  && apt-get install -y netcat-traditional git \
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
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /backend
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Expose the Django port
EXPOSE 8000

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Add permissions to the entrypoint script
RUN chmod +x /backend/entrypoint.sh

# Run Django's development server
CMD ["/bin/bash", "/backend/entrypoint.sh"]
