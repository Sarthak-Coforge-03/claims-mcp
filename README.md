# claims-mcp

An internal **IT equipment request handler**. An MCP server exposes tools over mock employee and policy data. A ReAct agent uses those tools to approve or deny equipment requests, or to escalate unclear ones to a human reviewer.

> Status: runs end to end. The MCP server (4 tools, 3 prompt templates) and the agent (plan, ReAct loop, reflection) are done; `docker compose run --build --rm cli` runs the whole app.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker with Compose v2), the main way to develop and run the project.
- [uv](https://docs.astral.sh/uv/) 0.12.x on your machine, to add dependencies and for editor autocomplete.

## Quick start (Docker)

```bash
cp .env.example .env                # then fill in the Foundry resource and API key
docker compose run --build --rm cli # build the image, start the server, open the CLI
docker compose down                 # stop the server afterwards
```

The CLI asks whether you are an employee or a contractor, then your employee ID (or a contractor's name), then what you need. It runs the agent and prints the result, then offers another request.

## Commands

| Task | Command |
|------|---------|
| Run the app | `docker compose run --build --rm cli` |
| Run all tests | `docker compose run --rm dev uv run pytest` |
| Run one test (`--no-cov` skips the 80% floor) | `docker compose run --rm dev uv run pytest --no-cov tests/host/agent/test_build_state.py::test_build_state_employee_requester_is_the_employee_id` |
| HTML coverage report | `docker compose run --rm dev uv run pytest --cov-report=html`, then open `htmlcov/index.html` |
| Lint + auto-fix / format | `docker compose run --rm dev uv run ruff check --fix .` / `... ruff format .` |
| Shell in the container | `docker compose run --rm dev bash` |
| Start / stop the server | `docker compose up -d --build --wait mcp_server` / `docker compose down` |
| Smoke client (server running) | `docker compose run --rm dev uv run python -m claims_mcp.host.gateways.smoke_client` |
| One request, no prompts (server running) | `uv run python -m claims_mcp.host.agent.run_demo` (scenario 1), or `... run_demo employee E004 "three monitors"`, `... run_demo contractor "Alex Doe" "a laptop"` |
| Check the LLM wiring | `uv run python -m claims_mcp.host.llm.llm_smoke` |

To inspect the server by hand: `npx @modelcontextprotocol/inspector`, transport **Streamable HTTP**, URL `http://localhost:8000/mcp`.

## How the agent works

The host agent (`src/claims_mcp/host/`) keeps one shared `AgentState`; each phase is its own model call with its own system prompt and sees only a view of that state.

- **Plan** (once): SELECT picks the server's scenario template (MCP prompt) that fits the request; with no fit, WRITE drafts a plan from the tool descriptions.
- **ReAct loop**: THINK chooses the next action or finishes with a decision (it is the only phase that routes), ACT makes that one tool call, OBSERVE states what the result establishes. It stops when THINK finishes or after `CLAIMS_MCP_MAX_REACT_STEPS` cycles.
- **Reflection** (once): two code checks, then CRITIQUE compares the draft with every tool result; REVISE runs only if the critique fails. Its result is final.

Rule IDs (POL / ELG / ESC / DEN) and the acceptance scenarios are in [`docs/requirements.md`](docs/requirements.md).

## Configuration

Settings come from environment variables, or a `.env` file in the repo root (`src/claims_mcp/settings.py`, pydantic-settings). All are optional; copy [`.env.example`](.env.example) to `.env` to change them.

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLAIMS_MCP_EMPLOYEES_FILE` | `data/employees.json` | Employee records read by the backend |
| `CLAIMS_MCP_POLICIES_FILE` | `data/policies.json` | Role policies (what each role may hold, how often) |
| `CLAIMS_MCP_ESCALATIONS_FILE` | `data/escalations.json` | Escalations saved by `flag_for_human_review` (created on first use, gitignored) |
| `CLAIMS_MCP_SERVER_HOST` | `127.0.0.1` | Interface the server listens on (compose sets `0.0.0.0`) |
| `CLAIMS_MCP_SERVER_PORT` | `8000` | Port the server listens on |
| `CLAIMS_MCP_SERVER_URL` | `http://localhost:8000/mcp` | Where clients connect (compose's `dev` and `cli` use `http://mcp_server:8000/mcp`) |
| `CLAIMS_MCP_FOUNDRY_RESOURCE` | (none) | Azure Foundry resource hosting Claude; set in `.env` |
| `CLAIMS_MCP_FOUNDRY_API_KEY` | (none) | API key for that resource; set in `.env` only |
| `CLAIMS_MCP_MODEL_DEPLOYMENT` | `claude-opus-5-5-fast` | Foundry deployment the agent calls |
| `CLAIMS_MCP_MODEL_EFFORT` | `medium` | How much the model thinks (`low` … `max`) |
| `CLAIMS_MCP_MAX_REACT_STEPS` | `5` | Most THINK → ACT → OBSERVE cycles before the agent stops (at least 1) |
| `CLAIMS_MCP_SHOW_TRACE` | `true` | `true` prints the whole run (plan, steps, reflection); `false` only the final decision |

Paths are relative to the working directory: the repo root on the host, `/app` in Docker.

## Docker setup

- [`compose.yaml`](compose.yaml) has three services on one image (the [`Dockerfile`](Dockerfile)'s `dev` stage): `dev` for tests and one-off commands, `mcp_server`, and `cli`, which starts the server and waits until it is healthy.
- `mcp_server` and `cli` run the code copied into the image, so they need a rebuild to pick up edits (`--build` in the commands above does it; only changed layers rebuild).
- Only `dev` mounts the repo at `/app`, so the test hook sees edits and ruff's fixes land on your files without a rebuild; the venv lives in `/opt/venv`, outside the mount.
- The server's `data/` is the named volume `claims_data`, seeded from the image's two JSON files. Escalations and data edits persist until `docker compose down -v`; edits to `data/*.json` only reach it after a rebuild and `down -v`.
- Both files are commented; read them for the details.

### Adding a dependency

```bash
uv add <package>          # runtime dependency (dev-only: uv add --dev <package>)
docker compose build      # bake the new lockfile into the image
```

Commit both `pyproject.toml` and `uv.lock`.

## Running without Docker

```bash
uv sync                                          # create .venv and install everything
uv run pytest                                    # tests + coverage
uv run python -m claims_mcp.mcp_server.server    # terminal 1: the server
uv run claims-mcp                                # terminal 2: the CLI
```

## Tests and continuous integration

Tests live in `tests/`, mirroring `src/`, and follow TDD. Coverage (line and branch) prints on every run and must stay at 80% or more (`pyproject.toml`). Both workflows run only on pull requests:

| Workflow | What it does |
|----------|--------------|
| [`ci.yml`](.github/workflows/ci.yml) | Builds the `dev` image, then runs `ruff check`, `ruff format --check` and `pytest` in it |
| [`claude-review.yml`](.github/workflows/claude-review.yml) | Claude reviews the PR with inline comments and one summary |

The Claude review needs the Claude GitHub App and an `ANTHROPIC_API_KEY` repository secret; `/install-github-app` in Claude Code sets up both.

## Project layout

```
src/claims_mcp/
  settings.py       configuration from CLAIMS_MCP_* environment variables
  backend/          business domain, no MCP: models/, repositories/ (base/ + json/), services/
  mcp_server/       MCP server exposing backend services as tools and prompts
  host/             the agent: agent/ (cli, run_agent, run_demo, trace printer), llm/, gateways/,
                    state/, plan/, react/, reflect/; reaches the backend only through MCP
data/               seed data (employees.json, policies.json)
docs/               requirements and policy rules
tests/              unit tests mirroring src/; test doubles in tests/fakes/
Dockerfile          image (base → dev)
compose.yaml        dev, mcp_server and cli services
.github/workflows/  CI and Claude PR review
```
