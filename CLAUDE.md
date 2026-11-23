# CLAUDE.md

Guidance for Claude Code (claude.ai/code) in this repository.

## What this is
An internal **IT equipment request handler**: an MCP server over mock employee/policy data, plus a ReAct agent (MCP client, Claude via `anthropic` SDK) that approves, denies, or escalates requests. Repo name says "claims" but the domain is equipment requests.

## Target architecture (in progress — update as it lands)
- MCP tools (each a thin wrapper over a plain, unit-tested function):
  - `get_employee_info(employee_id)` → role, tenure, equipment on file
  - `get_policy_limits(role)` → eligible items and refresh intervals
  - `check_request_eligibility(employee_id, item)` → within policy or not
  - `flag_for_human_review(employee_id, request, reason)` → side-effecting escalation
- Agent: explicit Thought → Action → Observation trace, then a reflection pass checking the draft against tool observations before finalizing. Escalate ambiguous/out-of-policy cases rather than guessing.
- Policy rules and escalation triggers are defined in `docs/requirements.md`.

## Conventions
- **TDD:** write the failing test first, then the code to make it pass. Build order: test → plain function → wrap as MCP tool → call via client. Unit tests hit functions directly, not the MCP protocol; cover normal and edge cases (e.g. unknown employee ID).
- Readability over concision: descriptive names, docstrings on every function and test, no `*`/`**` unpacking or multi-name unpacking of results.
- Never read or print `.env` files (`ANTHROPIC_API_KEY` lives there); `.env.example` is fine. Hooks in `.claude/`: `block-env.sh` blocks `.env*` access, `run-tests.sh` runs pytest after any `.py` edit.

## Commands (`uv` for everything)
- Sync env: `uv sync` · Add dep: `uv add <pkg>` (dev: `uv add --dev <pkg>`)
- Run entry point: `uv run claims-mcp` (`claims_mcp:main`, exported from `src/claims_mcp/__init__.py`)
- Tests (`tests/`): `uv run pytest` · single: `uv run pytest path/to/test_file.py::test_name`
- Coverage (pytest-cov, branch) prints on every run; HTML report: `uv run pytest --cov-report=html` → `htmlcov/`
- CI: GitHub Actions runs `uv sync` + `uv run pytest` (to be added).

Python 3.12, `uv_build` backend, src layout under `src/claims_mcp/`.
