"""Demo script that uses the MCP client to create objects, relationships, and query them.

This script relies on the project's environment configuration and the MCP
client. Set `LOG_LEVEL` in your .env or environment to enable logging.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from smoke.config import load_settings
from smoke.mcp_client import SurrealMcpStdioClient, extract_text_content

logger = logging.getLogger(__name__)


async def run_demo() -> None:
    try:
        settings = load_settings()
    except Exception as exc:  # pragma: no cover - simple runtime guard
        print("Failed to load settings:", exc)
        raise

    client = SurrealMcpStdioClient(settings)

    async with client.connect():
        await client.initialize()
        await client.send_initialized_notification()

        # Create two demo records
        id_a = f"demo_{uuid.uuid4().hex[:8]}"
        id_b = f"demo_{uuid.uuid4().hex[:8]}"

        create_a = f"CREATE demo:{id_a} CONTENT {{ name: 'Alice', role: 'author' }};"
        create_b = f"CREATE demo:{id_b} CONTENT {{ name: 'Bob', role: 'reader' }};"

        logger.debug("Creating record A: %s", create_a)
        res_a = await client.call_tool("query", {"query": create_a})
        logger.info("Created A: %s", extract_text_content(res_a))

        logger.debug("Creating record B: %s", create_b)
        res_b = await client.call_tool("query", {"query": create_b})
        logger.info("Created B: %s", extract_text_content(res_b))

        # Create a relationship from B -> A using RELATE syntax
        relate_q = f"RELATE demo:{id_b}->follows->demo:{id_a};"
        logger.debug("Creating relationship with: %s", relate_q)
        rel_res = await client.call_tool("query", {"query": relate_q})
        logger.info("Relationship created: %s", extract_text_content(rel_res))

        # Query B and expand the linked `follows` field
        select_b = f"SELECT *, follows.* FROM demo:{id_b};"
        logger.debug("Querying record B: %s", select_b)
        select_res = await client.call_tool("query", {"query": select_b})
        logger.info("Select result: %s", extract_text_content(select_res))

        # Cleanup
        logger.debug("Cleaning up demo records %s and %s", id_a, id_b)
        await client.call_tool("query", {"query": f"DELETE demo:{id_a};"})
        await client.call_tool("query", {"query": f"DELETE demo:{id_b};"})
        logger.info("Demo finished and cleaned up")


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
