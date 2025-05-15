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

# Upgrade pip
RUN pip install --upgrade pip

# Copy the Django project  and install dependencies
COPY requirements.txt  /backend/

# Run this command to install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project to the container
COPY . /backend/

# Add permissions to the entrypoint script
RUN chmod +x /backend/entrypoint.sh

# Expose the Django port
EXPOSE 8000

# Run Django’s development server
ENTRYPOINT ["/bin/bash", "/backend/entrypoint.sh"]