"""Pytest fixtures and test setup for the smoke tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from smoke.config import SmokeSettings, load_settings  # noqa: E402
from smoke.mcp_client import SurrealMcpStdioClient  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Run anyio-marked tests on asyncio backend."""
    return "asyncio"


@pytest.fixture(scope="session")
def smoke_settings() -> SmokeSettings:
    """Load and return smoke test settings for the test session."""
    return load_settings()


@pytest.fixture
def mcp_client(smoke_settings: SmokeSettings) -> SurrealMcpStdioClient:
    """Provide a `SurrealMcpStdioClient` instance for individual tests."""
    return SurrealMcpStdioClient(smoke_settings)
