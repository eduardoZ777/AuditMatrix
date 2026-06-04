FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging configuration and install dependencies
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py
RUN pip install .

# Copy application files
COPY app/ ./app
COPY main.py ./

# Create directory for logs
RUN mkdir -p logs

CMD ["python", "main.py"]
