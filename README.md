# claims-mcp

An internal **IT equipment request handler**. An MCP server exposes tools over mock employee and policy data. A ReAct agent then uses those tools to approve or deny equipment requests, or to escalate unclear ones to a human reviewer.

> Status: early setup. The project, the test tooling and the Docker dev environment are in place. The MCP server and the agent are not built yet.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker with Compose v2). This is the main way to develop and run the project.
- [uv](https://docs.astral.sh/uv/) 0.12.x on your machine. You need it to add dependencies and for editor autocomplete.

## Quick start (Docker)

```bash
# 1. Build the dev image (installs the locked dependencies from uv.lock)
docker compose build

# 2. Run the test suite inside the container (prints a coverage report)
docker compose run --rm dev uv run pytest
```

`docker compose run --rm dev <command>` runs any command in a throwaway container and removes the container when the command finishes.

## Everyday usage

| Task | Command |
|------|---------|
| Run all tests | `docker compose run --rm dev uv run pytest` |
| Run one test | `docker compose run --rm dev uv run pytest tests/test_sanity.py::test_sanity_always_passes` |
| HTML coverage report | `docker compose run --rm dev uv run pytest --cov-report=html`, then open `htmlcov/index.html` |
| Lint + auto-fix | `docker compose run --rm dev uv run ruff check --fix .` |
| Format code | `docker compose run --rm dev uv run ruff format .` |
| Shell inside the container | `docker compose run --rm dev bash` |
| Run the entry point | `docker compose run --rm dev uv run claims-mcp` |

### Editing code

The repo is mounted into the container at `/app`, so changes you make on your machine show up in the container straight away. **No rebuild is needed for code changes.**

### Adding a dependency

Dependencies are managed with uv on your machine. Rebuild the image afterwards:

```bash
uv add <package>          # runtime dependency
uv add --dev <package>    # dev-only (tests, tooling)
docker compose build      # bake the new lockfile into the image
```

Commit both `pyproject.toml` and `uv.lock`.

## How the Docker setup works

| File | Purpose |
|------|---------|
| [`Dockerfile`](Dockerfile) | Multi-stage build. **`base`**: Python 3.12-slim, uv and runtime dependencies, with no code or dev tools. **`dev`**: base plus dev dependencies, source and tests. Dependencies are installed in cached layers before code is copied. The virtualenv lives at `/opt/venv`, outside the mounted `/app`. |
| [`compose.yaml`](compose.yaml) | One `dev` service: builds the `dev` stage and mounts the repo at `/app`. |
| [`.dockerignore`](.dockerignore) | Keeps the local `.venv`, `.git`, secrets (`.env*`) and generated files out of the image. |

Both files are commented line by line; read them for the details.

## Running without Docker (optional)

```bash
uv sync              # create .venv and install everything
uv run pytest        # tests + coverage
```

## Configuration

Settings are read from environment variables, or from a `.env` file in the repo root, by `src/claims_mcp/settings.py` (pydantic-settings). Every variable is optional. Copy [`.env.example`](.env.example) to `.env` to change them.

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLAIMS_MCP_EMPLOYEES_FILE` | `data/employees.json` | Employee records read by the backend |
| `CLAIMS_MCP_POLICIES_FILE` | `data/policies.json` | Role policies (what each role may hold, how often) |

Paths are relative to the working directory: the repo root on the host, `/app` in Docker.

## Tests and coverage

- Tests live in `tests/` and run with pytest. Coverage (line and branch, via pytest-cov) is printed on every run. It is configured in `pyproject.toml`.
- Development follows TDD: write the failing test first, then the code to make it pass.

## Continuous integration

Both workflows run **only on pull requests** (opened, new commits, reopened):

| Workflow | What it does |
|----------|--------------|
| [`ci.yml`](.github/workflows/ci.yml) | Builds the `dev` Docker image, then runs `ruff check`, `ruff format --check` and `pytest` inside it, the same commands as locally. |
| [`claude-review.yml`](.github/workflows/claude-review.yml) | Claude reviews the PR and leaves inline comments plus one summary comment. |

One-time setup for the Claude review: install the Claude GitHub App and add an `ANTHROPIC_API_KEY` repository secret. Running `/install-github-app` in Claude Code does both.

## Project layout

```
src/claims_mcp/
  settings.py       configuration from CLAIMS_MCP_* environment variables
  backend/          business domain, no MCP: models/, repositories/ (base/ + json/; SQL optional later), services/
  mcp_server/       MCP server exposing backend services as tools
  client/           MCP client code; smoke check: uv run python -m claims_mcp.client.smoke_client
  agent/            (coming) ReAct agent; talks to the backend only through MCP
data/               mock data (employees.json, policies.json)
tests/              unit tests, mirroring src/ (tests/backend/...); test doubles in tests/fakes/
Dockerfile          dev image (multi-stage: base → dev)
compose.yaml        dev container definition
.github/workflows/  CI (tests) and Claude PR review
```
