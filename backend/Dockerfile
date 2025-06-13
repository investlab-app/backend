# Use the official Python runtime image
FROM python:3.13

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

# Copy the project files
COPY . /backend/

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install ".[dev]"

# Add permissions to the entrypoint script
RUN chmod +x /backend/entrypoint.sh

# Expose the Django port
EXPOSE 8000

# Run Django's development server
ENTRYPOINT ["/bin/bash", "/backend/entrypoint.sh"]