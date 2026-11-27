# claims-mcp

An internal **IT equipment request handler**. An MCP server exposes tools over mock employee and policy data. A ReAct agent then uses those tools to approve or deny equipment requests, or to escalate unclear ones to a human reviewer.

> Status: the MCP server (4 tools, 3 prompt templates, Streamable HTTP) is done. The agent's ReAct loop runs end to end; its plan and reflection steps are not built yet.

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
| `CLAIMS_MCP_ESCALATIONS_FILE` | `data/escalations.json` | Escalations saved by `flag_for_human_review` (created on first use, gitignored) |
| `CLAIMS_MCP_SERVER_HOST` | `127.0.0.1` | Interface the MCP server listens on (compose sets `0.0.0.0`) |
| `CLAIMS_MCP_SERVER_PORT` | `8000` | Port the MCP server listens on |
| `CLAIMS_MCP_SERVER_URL` | `http://localhost:8000/mcp` | Where clients connect (compose's `dev` uses `http://mcp_server:8000/mcp`) |
| `CLAIMS_MCP_FOUNDRY_RESOURCE` | (none) | Azure Foundry resource hosting Claude; set in `.env` |
| `CLAIMS_MCP_FOUNDRY_API_KEY` | (none) | API key for that resource; set in `.env` only |
| `CLAIMS_MCP_MODEL_DEPLOYMENT` | `claude-opus-5-5-fast` | Foundry deployment the host agent calls |
| `CLAIMS_MCP_MODEL_EFFORT` | `medium` | How much the model thinks (`low` … `max`) |
| `CLAIMS_MCP_MAX_REACT_STEPS` | `5` | Most THINK → ACT → OBSERVE cycles before the agent stops (at least 1) |

Paths are relative to the working directory: the repo root on the host, `/app` in Docker.

## Running the MCP server

The server speaks MCP over Streamable HTTP at `http://localhost:8000/mcp` and runs until stopped.
The smoke client connects to it, lists the tools and calls `get_employee_info` once.

```bash
# Docker
docker compose up -d mcp_server     # start in the background; `docker compose ps` shows "healthy"
docker compose run --rm dev uv run python -m claims_mcp.client.smoke_client
docker compose down                 # stop it

# Host (two terminals)
uv run python -m claims_mcp.mcp_server.server
uv run python -m claims_mcp.client.smoke_client
```

To inspect it by hand, run `npx @modelcontextprotocol/inspector`. Pick the **Streamable HTTP**
transport, enter the URL `http://localhost:8000/mcp`, then use the Tools and Prompts tabs.

## Running the agent

The host agent (`src/claims_mcp/host/`) keeps one shared `AgentState` for the whole run. Each
phase is its own model call, with its own system prompt, and sees only a view of that state:
- **THINK** (structured output, no tools) sees the request, today's date, the tool catalog and
  every earlier step's observation. It continues with one next action, or finishes with the
  final answer. It is the only phase that chooses where the run goes.
- **ACT** (with the tools) sees the request and THINK's next action, and makes that one tool
  call. A reply without exactly one call is recorded as an action error; the run continues.
- **OBSERVE** (no tools) sees the call and its raw result, and states what the result establishes.

ACT → OBSERVE → THINK is fixed by code. The run stops when THINK finishes, or after
`CLAIMS_MCP_MAX_REACT_STEPS` cycles. The trace is printed from the finished state.

It needs the Foundry settings in `.env` (see Configuration) and a running server:

```bash
uv run python -m claims_mcp.host.llm_smoke     # one model call, no tools: checks the LLM wiring
docker compose up -d --wait mcp_server
uv run python -m claims_mcp.host.run_demo      # scenario 1, prints Thought / Action / Observation
docker compose down
```

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
  host/             ReAct agent: llm/ adapter, tools/ MCP gateway, state/, react/ nodes + loop,
                    system_prompts/; talks to the backend only through MCP
data/               mock data (employees.json, policies.json)
tests/              unit tests, mirroring src/ (tests/backend/...); test doubles in tests/fakes/
Dockerfile          dev image (multi-stage: base → dev)
compose.yaml        dev container definition
.github/workflows/  CI (tests) and Claude PR review
```
