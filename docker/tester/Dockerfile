FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required for psycopg2
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY alembic.ini .
COPY migrations migrations/
COPY src src/

# Add src to Python path
ENV PYTHONPATH=/app/src

# Create entrypoint script
RUN printf '#!/bin/sh\necho "Running database migrations..."\nalembic upgrade head\necho "Starting service..."\nexec python -m proxy_rotator.apps.tester\n' > /entrypoint.sh && chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"] 