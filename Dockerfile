# Dockerfile for Ticket Watchdog service

FROM python:3.11-slim

# Install build tools and libpq for psycopg[binary]
RUN apt-get update \
 && apt-get install -y gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all requirement files
COPY requirements/ ./requirements/

# Install production and test dependencies
RUN pip install --no-cache-dir -r requirements/test.txt

# Copy the application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Default command to start the API
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
