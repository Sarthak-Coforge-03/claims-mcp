"""App configuration, read from environment variables and an optional .env file.

Every setting can be overridden with a CLAIMS_MCP_-prefixed variable (see .env.example).
Paths are relative to the working directory: the repo root on the host, /app in Docker.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration values for the backend, loaded once per process via get_settings()."""

    # extra="ignore": other keys in .env (e.g. ANTHROPIC_API_KEY for the host) don't break loading.
    model_config = SettingsConfigDict(env_prefix="CLAIMS_MCP_", env_file=".env", extra="ignore")

    employees_file: Path = Path("data/employees.json")
    policies_file: Path = Path("data/policies.json")


@lru_cache
def get_settings() -> Settings:
    """Return the shared Settings, read from the environment on the first call.

    Returns:
        The Settings instance for this process.
    """
    return Settings()
