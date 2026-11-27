# CLAUDE.md

Guidance for Claude Code (claude.ai/code) in this repository.

## What this is
An internal **IT equipment request handler**: an MCP server over mock employee/policy data, plus a ReAct agent (MCP client, Claude via `anthropic` SDK) that approves, denies, or escalates requests. Repo name says "claims" but the domain is equipment requests.

## Architecture (server done; agent plan → ReAct loop → reflection done; evidence runs next)
- MCP tools in `mcp_server/server.py`, each a thin wrapper over a unit-tested backend service (Employee/Policy/Eligibility/EscalationService), with agent-facing `description=` and `Annotated` argument descriptions:
  - `get_employee_info(employee_id)` → role, hire_date, equipment on file
  - `get_policy_limits(role)` → item policies (policy_rule_id, max_held, refresh_interval_months)
  - `check_request_eligibility(employee_id, item)` → rule_id (ELG-1/2/3, DEN-2, ESC-2) + policy_rule_id
  - `flag_for_human_review(employee_id, request, reason)` → side-effecting escalation
- MCP prompts: templates for known scenarios only (`replacement_request`, `new_item_request`, `exception_request`, built in `mcp_server/prompts/`; shared opening checks ESC-1/3/4 in `shared_steps.py`, bullets not numbers). No match → the planner works from the tool descriptions.
- Agent: explicit Thought → Action → Observation trace, then a reflection pass checking the draft against tool observations before finalizing. Escalate ambiguous/out-of-policy cases rather than guessing. Rule IDs (POL/ELG/ESC/DEN) are defined in `docs/requirements.md`.

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

Python 3.12, `uv_build`. Config: `settings.py` (pydantic-settings, `CLAIMS_MCP_*` env vars, see `.env.example`). Layers in `src/claims_mcp/`: `backend/` (`models/`, `repositories/base/` ABCs + `repositories/json/` impls, SQL optional later; `services/`; never imports MCP; test fakes live in `tests/fakes/`) · `mcp_server/` (MCP adapter over Streamable HTTP at `http://localhost:8000/mcp`; run: `uv run python -m claims_mcp.mcp_server.server`, Docker: `docker compose up -d mcp_server`) · `client/` (MCP client code; smoke check, server running: `uv run python -m claims_mcp.client.smoke_client`) · `host/` (the agent: `llm/` provider-neutral models + `adapters/` (base, Foundry Claude), `tools/` and `templates/` gateways (base, MCP; tools and MCP prompts), `state/` one shared pydantic `AgentState`, `plan/` node (SELECT a template, else WRITE a plan; runs once), `react/` per-phase `views.py` + THINK/ACT/OBSERVE nodes + `react_loop.py` driver, `system_prompts/` one per model call, `reflect/` (2 code checks + CRITIQUE, then REVISE only if the critique fails; runs once, result final), `run_agent.py` = plan → loop → reflection; THINK alone routes, code forces ACT → OBSERVE → THINK; demo, server running: `uv run python -m claims_mcp.host.run_demo ["request"]`). `client/` and `host/` reach the backend only via MCP. One class per file, base classes in their own file, no folder per class.
