# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

# Build stage
FROM dhi.io/python:3.14.2-alpine3.22-dev@sha256:76554f88f167cc7a78791938173b7803824bf2b25df754f9b5a49fd082dbd309 AS builder

# Install uv
COPY --from=astral/uv:0.9.18-python3.12-alpine@sha256:ba8fc3d26628bc566eda4ed792608c42da7093e5b8f941d6260098919a74346c /usr/local/bin/uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Interestingly, uv build and uv install will look at VIRTUAL_ENV but not uv venv
ENV VIRTUAL_ENV=/venv
# Install dependencies in a separate layer (cached when lock file unchanged)
RUN uv venv /venv && uv sync --frozen --no-install-project --no-dev

# Copy source code (changes frequently)
COPY . ./

# building a wheel and installing it is needed instead of a simple uv sync because
# uv sync will link src into the venv python path
RUN uv build --wheel && uv pip install dist/*.whl

# Runtime stage
FROM dhi.io/python:3.14.2-alpine3.22-dev@sha256:76554f88f167cc7a78791938173b7803824bf2b25df754f9b5a49fd082dbd309

COPY --from=builder /venv /venv

USER nonroot
EXPOSE 8080
CMD ["/venv/bin/flask-lab"]
