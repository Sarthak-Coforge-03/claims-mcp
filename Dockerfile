# Multi-stage Dockerfile for claims-mcp.
#
# A "stage" starts at each FROM. Later stages build on earlier ones by name, and
# `--target <stage>` (or `target:` in compose.yaml) picks which stage to build.
#
#   base  Python 3.12 + uv + runtime dependencies. No project code, no dev tools.
#         Shared foundation that every other stage builds on.
#   dev   base + dev dependencies (pytest, pytest-cov) + source + tests.
#         Used for development, the test hook and CI.
#
# Later stages (e.g. `server`, `agent`) will also start `FROM base`, so they reuse its
# cached layers instead of reinstalling Python, uv and the shared dependencies.


# ---------------------------------------------------------------------------------------
# Stage: base
# ---------------------------------------------------------------------------------------
# Base image: slim Debian with Python 3.12, matching .python-version on the host.
# "AS base" names this stage so later stages can say `FROM base`.
FROM python:3.12-slim AS base

# Copy the uv binaries out of uv's official image (no curl/pip install needed).
# Pinned to the same uv version the host uses, so uv.lock is read the same way everywhere.
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

# UV_PROJECT_ENVIRONMENT: put the virtualenv in /opt/venv, OUTSIDE /app. compose mounts the
#   host repo over /app, which would hide a venv stored there (and the host's .venv holds macOS
#   binaries that cannot run in this Linux container).
# UV_LINK_MODE=copy: copy files into the venv instead of hard-linking (avoids warnings across filesystems).
# UV_COMPILE_BYTECODE=1: precompile .pyc files at build time, so the container starts faster.
# PATH: put the venv's bin first, so plain `python` / `pytest` use the project's environment.
# ENV values are inherited by every stage built FROM base.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# All following commands run from /app; this is where the project code lives in the container.
WORKDIR /app

# Copy ONLY the dependency manifests. Docker caches each step (layer); this layer changes
# only when dependencies change, so editing code or docs later does not trigger a reinstall.
# (README.md is deliberately NOT copied here: installing dependencies alone does not need it,
# and copying it would make every docs edit reinstall all dependencies.)
COPY pyproject.toml uv.lock ./

# Install the RUNTIME dependencies exactly as locked:
#   --locked              fail if uv.lock is out of date with pyproject.toml
#   --no-install-project  skip the project itself (its source is not copied in this stage)
#   --no-dev              skip the dev group (pytest etc.); dev tools are added in the dev stage
RUN uv sync --locked --no-install-project --no-dev


# ---------------------------------------------------------------------------------------
# Stage: dev
# ---------------------------------------------------------------------------------------
# Start from everything base already built (Python, uv, ENV, WORKDIR, runtime deps).
FROM base AS dev

# Add the dev dependency group on top of base's runtime deps. Still no project code, so
# this layer stays cached until pyproject.toml / uv.lock change.
RUN uv sync --locked --no-install-project

# Now copy the source and tests. Code changes only rebuild from this step onwards.
# README.md comes along here because building the project package needs it
# (pyproject.toml has readme = "README.md").
COPY README.md ./
COPY src ./src
COPY tests ./tests

# Install the project itself (editable, pointing at /app/src). Dependencies are already cached above.
RUN uv sync --locked

# Default command when the container runs with no command given: run the test suite.
CMD ["uv", "run", "pytest"]
