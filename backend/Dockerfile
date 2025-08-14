FROM ghcr.io/astral-sh/uv:python3.13-bookworm

RUN apt-get update \
  && apt-get install -y --no-install-recommends netcat-traditional git \
  && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
  && apt-get clean

# Create non-root user to run the app
RUN groupadd -g 1000 app \
  && useradd -m -u 1000 -g app -s /bin/bash app \
  && mkdir -p /backend /backend/staticfiles /home/app/.cache/uv \
  && chown -R app:app /backend /home/app/.cache/uv

# Switch to the non-root user
USER app

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
RUN --mount=type=cache,target=/home/app/.cache/uv,uid=1000,gid=1000 \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --locked --no-install-project

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY --chown=app:app . /backend
RUN --mount=type=cache,target=/home/app/.cache/uv,uid=1000,gid=1000 \
  uv sync --locked

# Expose the Django port
EXPOSE 8000

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Add permissions to the entrypoint script
RUN chmod +x /backend/entrypoint.sh

# Add a healthcheck to verify the app responds on /api/status
HEALTHCHECK --start-period=20s \
  CMD python -c "import sys,urllib.request; \
  url='http://127.0.0.1:8000/api/status'; \
  resp=urllib.request.urlopen(url, timeout=3); \
  sys.exit(0 if 200 <= resp.getcode() < 300 else 1)" || exit 1

# Run Django's development server
CMD ["/bin/bash", "/backend/entrypoint.sh"]
