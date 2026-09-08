FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# uv is copied from its official image, so the development container does not
# install project packages with pip since uv is faster.
COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /uvx /bin/

WORKDIR /workspace

# Install dependencies in /opt/venv. VS Code bind-mounts the project over
# /workspace later, so the environment remains available inside the container.
COPY pyproject.toml /tmp/cybersecurity-rag/pyproject.toml
WORKDIR /tmp/cybersecurity-rag
RUN uv sync --no-dev --no-install-project

WORKDIR /workspace

# Dev Containers overrides this command, but it also makes the image convenient
# to inspect manually without immediately starting Streamlit.
CMD ["sleep", "infinity"]

