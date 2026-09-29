# =============================================================================
# SecureVault - Dockerfile
# =============================================================================
# Production-ready image for the SecureVault Flask application.
# =============================================================================

# Use a slim Python 3.12 base image.
FROM python:3.12-slim

# Set environment variables to avoid Python bytecode and buffered output.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container.
WORKDIR /app

# Install system dependencies required by psycopg2.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the container.
COPY . .

# Expose the port the application runs on.
EXPOSE 5000

# Run the application with Gunicorn (production WSGI server).
# The health check endpoint is available at /health.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "run:app"]
