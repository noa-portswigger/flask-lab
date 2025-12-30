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
ENV VIRTUAL_ENV=/deps-venv
# Install dependencies in a separate layer (cached when lock file unchanged)
RUN uv venv /deps-venv && uv sync --frozen --no-install-project --no-dev --active

# Copy source code (changes frequently)
COPY . ./

RUN uv build --wheel
ENV VIRTUAL_ENV=/venv
RUN uv venv /venv && uv pip install --no-deps dist/*.whl

# Runtime stage
FROM dhi.io/python:3.14.2-alpine3.22-dev@sha256:76554f88f167cc7a78791938173b7803824bf2b25df754f9b5a49fd082dbd309

# This might look a little magical, but it will ensure that the files from deps-venv (created above)
# ends up in a separate layer, only updating it when needed.
COPY --from=builder /deps-venv /venv
COPY --from=builder /venv /venv

USER nonroot
EXPOSE 8080
CMD ["/venv/bin/flask-lab"]
