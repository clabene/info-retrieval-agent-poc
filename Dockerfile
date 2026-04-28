FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps)
RUN uv sync --no-dev --frozen

# Copy source code
COPY src/ ./src/
COPY main.py ingest.py ./
COPY data/ ./data/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "python", "main.py"]
