"""PlanSource: where the run's plan came from."""

from enum import StrEnum


class PlanSource(StrEnum):
    """mcp_template = a server scenario template fit the request; tool_descriptions = written."""

    MCP_TEMPLATE = "mcp_template"
    TOOL_DESCRIPTIONS = "tool_descriptions"
