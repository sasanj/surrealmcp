from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import json
from typing import Any

import mcp.types as types
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from smoke.config import SmokeSettings

logger = logging.getLogger(__name__)


class SurrealMcpStdioClient:
    def __init__(self, settings: SmokeSettings):
        self._settings = settings
        self._session: ClientSession | None = None
        logger.debug("SurrealMcpStdioClient initialized with settings: %s", settings)

    @asynccontextmanager
    async def connect(self) -> AsyncIterator["SurrealMcpStdioClient"]:
        server = StdioServerParameters(
            command=self._settings.server.command,
            args=self._settings.server.args,
            env=self._settings.server_env(),
            cwd=self._settings.server.cwd,
        )
        logger.debug("Connecting to server with command=%s args=%s cwd=%s", server.command, server.args, server.cwd)
        async with (
            stdio_client(server) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            logger.debug("Stdio client opened, creating ClientSession")
            self._session = session
            try:
                logger.debug("Client session established, yielding client")
                yield self
            finally:
                logger.debug("Closing client session")
                self._session = None

    async def initialize(self) -> types.InitializeResult:
        """Initialize the MCP session.

        Returns:
            The initialization result from the MCP server.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        logger.debug("Initializing MCP session")
        session = self._require_session()
        result = await session.initialize()
        logger.debug("Initialize result: %s", result)
        return result

    async def send_initialized_notification(self) -> None:
        """Send the initialized notification to the MCP server.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        logger.debug("Sending InitializedNotification to server")
        notification = types.ClientNotification(types.InitializedNotification())
        await self._require_session().send_notification(notification)
        logger.debug("InitializedNotification sent")

    async def list_tools(self) -> types.ListToolsResult:
        """List all available tools from the MCP server.

        Returns:
            The list of tools available on the server.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        logger.debug("Requesting tool list from server")
        result = await self._require_session().list_tools()
        logger.debug("List tools result: %s", result)
        return result

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
        logger.debug("Calling tool %s with arguments=%s", name, arguments)
        result = await self._require_session().call_tool(name, arguments)
        self._validate_json_content(name, result)
        logger.debug("Call tool %s result: %s", name, result)
        return result

    def _validate_json_content(self, tool_name: str, result: types.CallToolResult) -> None:
        """Ensure JSON tool payloads include a duration in milliseconds."""
        logger.debug("Validating JSON content for tool %s", tool_name)
        for item in result.content:
            text = getattr(item, "text", None)
            if not isinstance(text, str):
                continue

            try:
                payload: Any = json.loads(text)
            except json.JSONDecodeError:
                logger.debug("Tool %s returned non-JSON text content", tool_name)
                continue

            if not isinstance(payload, dict):
                logger.debug("Tool %s returned JSON content that is not an object", tool_name)
                continue

            duration_ms = payload.get("duration_ms")
            if not isinstance(duration_ms, int):
                logger.debug("Tool %s returned JSON without integer duration_ms: %s", tool_name, payload)
                raise RuntimeError(
                    f"Tool {tool_name} returned JSON content without integer duration_ms: {payload}"
                )

    def _require_session(self) -> ClientSession:
        logger.debug("Requiring active client session")
        if self._session is None:
            logger.debug("No active session found; raising RuntimeError")
            raise RuntimeError("MCP client session has not been opened.")
        logger.debug("Active session present")
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
    logger.debug("Extracting text content from CallToolResult: %s", result)
    for item in result.content:
        text = getattr(item, "text", None)
        if isinstance(text, str):
            logger.debug("Found text content (raw): %s", text)
            # Try to parse JSON text that the Rust server returns as an
            # array string (e.g. serialized Vec<String>). If parsing
            # succeeds and yields a list, return the parsed value so
            # callers can work with structured content.
            try:
                parsed: Any = json.loads(text)
            except Exception:
                logger.debug("Text content is not JSON; returning raw string")
                return text

            if isinstance(parsed, list):
                # Attempt to further parse each element if it's JSON-like;
                # otherwise keep the element as-is (usually Rust debug
                # formatted strings).
                parsed_elements: list[Any] = []
                for el in parsed:
                    if not isinstance(el, str):
                        parsed_elements.append(el)
                        continue
                    try:
                        nested = json.loads(el)
                    except Exception:
                        parsed_elements.append(el)
                    else:
                        parsed_elements.append(nested)
                logger.debug("Parsed text content into list with %d elements", len(parsed_elements))
                return parsed_elements

            # If it's JSON but not a list, return the parsed object.
            logger.debug("Parsed text content into JSON object")
            return parsed

    logger.debug("No text content found in CallToolResult")
    raise RuntimeError("CallToolResult did not contain text content.")
