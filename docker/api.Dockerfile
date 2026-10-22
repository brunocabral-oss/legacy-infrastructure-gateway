FROM python:3.12-slim

# Set environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging specifications
COPY pyproject.toml README.md NOTICE LICENSE /app/

# Install dependencies
RUN pip install --no-cache-dir .

# Copy source code and entrypoint
COPY src /app/src
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Re-install package in editable/link mode so entry points work
RUN pip install --no-cache-dir -e .

# Security: Create non-root user
RUN useradd -m -u 1000 liguser && chown -R liguser:liguser /app
USER liguser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "lig.main:app", "--host", "0.0.0.0", "--port", "8000"]
