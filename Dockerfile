# Build stage
FROM dhi.io/python:3.14.2-debian13-fips-dev AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Build the wheel
RUN uv build --wheel

# Create venv and install the wheel
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python --no-cache dist/*.whl

# Runtime stage
FROM dhi.io/python:3.14.2-debian13-fips

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use venv
ENV PATH="/opt/venv/bin:$PATH"

# Switch to non-root user
USER nonroot

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 8080

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "flask_lab:app"]
