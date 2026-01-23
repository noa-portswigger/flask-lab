# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

# Build stage
FROM dhi.io/alpine-base:3.23-dev AS builder

# Install uv
COPY --from=astral/uv:alpine /usr/local/bin/uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./
# Interestingly, uv build and uv install will look at VIRTUAL_ENV but not uv venv
ENV VIRTUAL_ENV=/deps-venv
# Since we are using the python version that uv pulls,
ENV UV_PYTHON_INSTALL_DIR=/python
# Install dependencies in a separate layer (cached when lock file unchanged)
RUN uv venv /deps-venv && uv sync --frozen --no-install-project --no-dev --active

# Copy source code (changes frequently)
COPY . ./

RUN uv build --wheel
ENV VIRTUAL_ENV=/venv
RUN uv venv /venv && uv pip install --no-deps dist/*.whl

# Runtime stage
FROM gcr.io/distroless/static-debian13

COPY --from=builder /python /python
# This might look a little magical, but it will ensure that the files from deps-venv (created above)
# ends up in a separate layer, only updating it when needed.
COPY --from=builder /deps-venv /venv
COPY --from=builder /venv /venv

USER nonroot
EXPOSE 8080
CMD ["/venv/bin/flask-lab"]
