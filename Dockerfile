# Multi-stage build setup
FROM python:3.11-slim as base

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
# Create a dummy folder to satisfy setuptools during base dependency build
RUN mkdir -p app && touch app/__init__.py
RUN pip install .

# Copy implementation files
COPY app/ ./app
COPY main.py dashboard.py ./

# Create directory to share logs
RUN mkdir -p logs

# Expose Streamlit default port
EXPOSE 8501
