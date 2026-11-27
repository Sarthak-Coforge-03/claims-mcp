# Two stages; compose builds `dev` (target: dev).
#   base  Python 3.12, uv and the runtime dependencies; no code, no dev tools.
#   dev   base + dev dependencies + source, tests and seed data.
# Layers go from least to most often changed, so a code edit never reinstalls dependencies.

# --- base -------------------------------------------------------------------------------
FROM python:3.12-slim AS base

# Same uv version as the host, so uv.lock is read the same way everywhere.
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

# The venv lives in /opt/venv because compose mounts the repo over /app (and the host's
# .venv holds macOS binaries). Copy mode avoids hard-link warnings across filesystems;
# precompiled bytecode starts faster; PATH makes plain `python` use the venv.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Only the manifests, so this layer changes only when dependencies do.
COPY pyproject.toml uv.lock ./
# Runtime dependencies exactly as locked; the project and dev group come later.
RUN uv sync --locked --no-install-project --no-dev

# --- dev --------------------------------------------------------------------------------
FROM base AS dev

# The dev group (pytest, ruff, ...), still cached until the manifests change.
RUN uv sync --locked --no-install-project

# README.md is needed to build the package (pyproject.toml's readme).
COPY README.md ./
COPY src ./src
COPY tests ./tests
# Seeds the claims_data volume on first use; escalations.json is runtime output, not copied.
COPY data/employees.json data/policies.json ./data/

# The project itself, editable against /app/src.
RUN uv sync --locked

CMD ["uv", "run", "pytest"]
