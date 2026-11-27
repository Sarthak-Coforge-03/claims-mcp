"""App configuration, read from environment variables and an optional .env file.

Every setting can be overridden with a CLAIMS_MCP_-prefixed variable (see .env.example).
Paths are relative to the working directory: the repo root on the host, /app in Docker.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the backend, MCP server and host LLM, loaded once via get_settings()."""

    # extra="ignore": other keys in .env (not CLAIMS_MCP_-prefixed) don't break loading.
    model_config = SettingsConfigDict(env_prefix="CLAIMS_MCP_", env_file=".env", extra="ignore")

    employees_file: Path = Path("data/employees.json")
    policies_file: Path = Path("data/policies.json")
    # Written at runtime by flag_for_human_review; gitignored, created on the first escalation.
    escalations_file: Path = Path("data/escalations.json")

    # MCP server over Streamable HTTP. 127.0.0.1 keeps it local and lets the SDK switch on its
    # DNS-rebinding protection; Docker sets 0.0.0.0 so other containers can reach it.
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    # Where clients (smoke client, host agent) connect; /mcp is the SDK's default endpoint.
    server_url: str = "http://localhost:8000/mcp"

    # Host LLM: Claude on Microsoft Foundry (Azure). The resource name and key live in .env only.
    # The client builds https://<resource>.services.ai.azure.com/anthropic/ from the resource name.
    foundry_resource: str = ""
    foundry_api_key: SecretStr | None = None
    # On Foundry, fast mode is its own deployment (the "-fast" suffix), not a request parameter.
    model_deployment: str = "claude-opus-5-5-fast"
    # Opus 5.5 always thinks; effort ("low".."max") sets how much. Its default is "medium".
    model_effort: str = "medium"
    # Most THINK → ACT → OBSERVE cycles per run; the longest scenario (lookup, eligibility,
    # escalation, then the finishing THINK) fits in 5. ge=1 rejects 0 when settings load.
    max_react_steps: int = Field(default=5, ge=1)
    # True prints the whole run (plan, steps, reflection); False prints only the final decision.
    # The state keeps the full record either way.
    show_trace: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return the shared Settings, read from the environment on the first call.

    Returns:
        The Settings instance for this process.
    """
    return Settings()
