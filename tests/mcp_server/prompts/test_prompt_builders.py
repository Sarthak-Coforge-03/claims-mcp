"""Unit tests for the prompt builders: the scenario templates the agent's plan step receives.

Builders are called directly as plain functions; the MCP prompt wiring is tested in test_prompts.py.
"""

from datetime import date

from claims_mcp.mcp_server.prompts.exception_request import build_exception_request_prompt
from claims_mcp.mcp_server.prompts.new_item_request import build_new_item_request_prompt
from claims_mcp.mcp_server.prompts.replacement_request import build_replacement_request_prompt
from claims_mcp.mcp_server.prompts.shared_steps import build_opening_checks

PROMPT_BUILDERS = [
    build_replacement_request_prompt,
    build_new_item_request_prompt,
    build_exception_request_prompt,
]


def test_every_prompt_starts_with_the_opening_checks():
    """Each template includes the unknown-employee, contractor and probation checks (ESC-1/3/4),
    since no tool result flags contractors or probation."""
    today = date(2026, 11, 26)
    opening_checks = build_opening_checks("E100", today)

    prompts_missing_checks = [
        build_prompt.__name__
        for build_prompt in PROMPT_BUILDERS
        if opening_checks not in build_prompt("E100", "laptop", "it is slow", "1", today)
    ]

    assert prompts_missing_checks == []


def test_every_prompt_fills_in_the_request():
    """Each template states its request: E100, laptop, quantity 3, the reason and the date."""
    today = date(2026, 11, 26)
    request_values = ["E100", "laptop", "Quantity: 3", "screen cracked", "Today: 2026-11-26"]

    prompts_missing_values = [
        build_prompt.__name__
        for build_prompt in PROMPT_BUILDERS
        if not all(
            value in build_prompt("E100", "laptop", "screen cracked", "3", today)
            for value in request_values
        )
    ]

    assert prompts_missing_values == []
