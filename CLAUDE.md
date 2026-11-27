# CLAUDE.md

Guidance for Claude Code (claude.ai/code) in this repository.

## What this is
An internal **IT equipment request handler**: an MCP server over mock employee/policy data, plus a ReAct agent (MCP client, Claude via `anthropic` SDK) that approves, denies, or escalates requests. Repo name says "claims" but the domain is equipment requests.

## Target architecture (in progress — update as it lands)
- MCP tools in `mcp_server/server.py`, each a thin wrapper over a unit-tested backend service method (`get_employee_info` → `EmployeeService`; the rest to come):
  - `get_employee_info(employee_id)` → role, tenure, equipment on file
  - `get_policy_limits(role)` → eligible items and refresh intervals
  - `check_request_eligibility(employee_id, item)` → within policy or not
  - `flag_for_human_review(employee_id, request, reason)` → side-effecting escalation
- Agent: explicit Thought → Action → Observation trace, then a reflection pass checking the draft against tool observations before finalizing. Escalate ambiguous/out-of-policy cases rather than guessing.
- Policy rules and escalation triggers are defined in `docs/requirements.md`.

## Conventions
- **TDD:** write the failing test first, then the code to make it pass. Build order: test → plain function → wrap as MCP tool → call via client. Unit tests hit functions directly, not the MCP protocol; cover normal and edge cases (e.g. unknown employee ID).
- Readability over concision: descriptive names, docstrings on every function and test, no `*`/`**` unpacking or multi-name unpacking of results.
- Never read or print `.env` files (`ANTHROPIC_API_KEY` lives there); `.env.example` is fine. Hooks in `.claude/`: `block-env.sh` blocks `.env*` access; after any `.py` edit `run-ruff.sh` formats + lints (ruff), `run-tests.sh` / `run-tests-docker.sh` run pytest on host / in Docker.

## Commands (develop in Docker; `uv` manages deps)
- Docker: `docker compose build` (again after dep changes) · tests: `docker compose run --rm dev uv run pytest` · shell: `docker compose run --rm dev bash`
- Sync env: `uv sync` · Add dep on host: `uv add <pkg>` (dev: `uv add --dev <pkg>`), then rebuild
- Run entry point: `uv run claims-mcp` (`claims_mcp:main`, exported from `src/claims_mcp/__init__.py`)
- Tests (`tests/`): `uv run pytest` · single: `uv run pytest path/to/test_file.py::test_name`
- Coverage (pytest-cov, branch) prints on every run; HTML report: `uv run pytest --cov-report=html` → `htmlcov/`
- Lint/format (ruff, config in `pyproject.toml`): `uv run ruff check --fix . && uv run ruff format .`

Python 3.12, `uv_build`. Config: `settings.py` (pydantic-settings, `CLAIMS_MCP_*` env vars, see `.env.example`). Layers in `src/claims_mcp/`: `backend/` (`models/`, `repositories/base/` ABCs + `repositories/json/` impls, SQL optional later; `services/`; never imports MCP; test fakes live in `tests/fakes/`) · `mcp_server/` (MCP adapter over Streamable HTTP at `http://localhost:8000/mcp`; run: `uv run python -m claims_mcp.mcp_server.server`, Docker: `docker compose up -d mcp_server`) · `client/` (MCP client code; smoke check, server running: `uv run python -m claims_mcp.client.smoke_client`) · `agent/` (later). `client/` and `agent/` reach the backend only via MCP. One class per file, base classes in their own file, no folder per class.
