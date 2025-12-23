# flask-lab

This is an example Flask project illustrating how modern Python build tooling and container image creation can be integrated.

## Overview

This project demonstrates a cohesive setup where:

- **uv** handles package building and dependency management
- **Multi-stage Docker builds** create minimal, reproducible container images

## Building and Running

```bash
# Build the Docker image
docker build -t flask-lab .

# Run the container
docker run -p 8080:8080 flask-lab

# Test the endpoint
curl localhost:8080
```

## Local Development

```bash
# Install dependencies
uv sync

# Run locally
uv run flask-lab
```

## License

MIT
