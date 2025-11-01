# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and add to PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.cargo/bin/uv /usr/local/bin/uv || mv /root/.local/bin/uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY README.md ./

# Set UV to use system Python (no virtual environment needed in Docker)
# This prevents "Directory not empty" errors when the backend volume is mounted.
ENV UV_SYSTEM_PYTHON=1

# Install dependencies with uv
RUN uv pip install -e .

# Expose port
EXPOSE 8000

# Run database migrations (includes seed data) and start the app
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
