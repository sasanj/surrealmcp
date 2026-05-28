"""MCP client implementation for SurrealDB smoke tests.

This module provides a stdio-based MCP client for testing SurrealDB MCP server
functionality, including initialization, tool listing, and tool execution.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import mcp.types as types
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from smoke.config import SmokeSettings


class SurrealMcpStdioClient:
    """A stdio-based MCP client for SurrealDB smoke tests.

    This class manages connections to a SurrealDB MCP server via stdio,
    providing methods for initialization, tool listing, and tool execution.
    """

    def __init__(self, settings: SmokeSettings):
        """Initialize the SurrealMCP stdio client.

        Args:
            settings: Configuration settings for the smoke test client.
        """
        self._settings = settings
        self._session: ClientSession | None = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[SurrealMcpStdioClient]:
        """Connect to the SurrealDB MCP server via stdio.

        Yields:
            The client instance for use in async context manager.

        Raises:
            Exception: If connection to the server fails.
        """
        server = StdioServerParameters(
            command=self._settings.server.command,
            args=self._settings.server.args,
            env=self._settings.server_env(),
            cwd=self._settings.server.cwd,
        )
        async with (
            stdio_client(server) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            self._session = session
            try:
                yield self
            finally:
                self._session = None

    async def initialize(self) -> types.InitializeResult:
        """Initialize the MCP session.

        Returns:
            The initialization result from the MCP server.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        return await self._require_session().initialize()

    async def send_initialized_notification(self) -> None:
        """Send the initialized notification to the MCP server.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        notification = types.ClientNotification(types.InitializedNotification())
        await self._require_session().send_notification(notification)

    async def list_tools(self) -> types.ListToolsResult:
        """List all available tools from the MCP server.

        Returns:
            The list of tools available on the server.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        return await self._require_session().list_tools()

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, object] | None = None,
    ) -> types.CallToolResult:
        """Call a tool on the MCP server.

        Args:
            name: The name of the tool to call.
            arguments: Optional arguments to pass to the tool.

        Returns:
            The result of the tool call.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        return await self._require_session().call_tool(name, arguments)

    def _require_session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("MCP client session has not been opened.")
        return self._session


def extract_text_content(result: types.CallToolResult) -> str:
    """Extract text content from a CallToolResult.

    Args:
        result: The tool call result to extract text from.

    Returns:
        The text content from the result.

    Raises:
        RuntimeError: If the result does not contain text content.
    """
    for item in result.content:
        text = getattr(item, "text", None)
        if isinstance(text, str):
            return text
    raise RuntimeError("CallToolResult did not contain text content.")
