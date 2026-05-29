from __future__ import annotations

import json
from uuid import uuid4

import pytest

from smoke.mcp_client import SurrealMcpStdioClient, extract_text_content


def _parse_query_payload(payload: object) -> dict[str, object]:
    if isinstance(payload, str):
        payload = json.loads(payload)
    assert isinstance(payload, dict)
    assert isinstance(payload.get("query"), str)
    assert isinstance(payload.get("duration_ms"), int)
    assert isinstance(payload.get("result"), list)
    return payload


@pytest.mark.anyio
async def test_query_tool_create_select_delete_roundtrip(
    mcp_client: SurrealMcpStdioClient,
) -> None:
    record_key = f"smoke_{uuid4().hex[:10]}"
    marker = f"marker_{uuid4().hex[:8]}"

    create_query = f"CREATE smoke_e2e:{record_key} CONTENT {{ marker: '{marker}', n: 42, source: 'smoke' }};"
    select_query = f"SELECT * FROM smoke_e2e:{record_key};"
    parameterized_query = "SELECT * FROM smoke_e2e WHERE marker = $marker LIMIT 1;"
    delete_query = f"DELETE smoke_e2e:{record_key};"

    async with mcp_client.connect():
        await mcp_client.initialize()

        try:
            create_result = await mcp_client.call_tool("query", {"query": create_query})
            create_payload = _parse_query_payload(extract_text_content(create_result))
            create_rows = create_payload["result"]
            assert isinstance(create_rows, list)
            assert create_rows
            first_create_row = create_rows[0]
            assert isinstance(first_create_row, dict)
            assert first_create_row.get("id") == f"smoke_e2e:{record_key}"
            assert first_create_row.get("marker") == marker
            assert first_create_row.get("n") == 42
            assert first_create_row.get("source") == "smoke"

            select_result = await mcp_client.call_tool("query", {"query": select_query})
            select_payload = _parse_query_payload(extract_text_content(select_result))
            select_rows = select_payload["result"]
            assert isinstance(select_rows, list)
            assert select_rows
            first_select_row = select_rows[0]
            assert isinstance(first_select_row, dict)
            assert first_select_row.get("id") == f"smoke_e2e:{record_key}"
            assert first_select_row.get("marker") == marker
            assert first_select_row.get("n") == 42
            assert first_select_row.get("source") == "smoke"

            parameterized_result = await mcp_client.call_tool(
                "query",
                {"query": parameterized_query, "parameters": {"marker": marker}},
            )
            parameterized_payload = _parse_query_payload(extract_text_content(parameterized_result))
            parameterized_rows = parameterized_payload["result"]
            assert isinstance(parameterized_rows, list)
            assert parameterized_rows
            first_parameterized_row = parameterized_rows[0]
            assert isinstance(first_parameterized_row, dict)
            assert first_parameterized_row.get("id") == f"smoke_e2e:{record_key}"
            assert first_parameterized_row.get("marker") == marker
        finally:
            await mcp_client.call_tool("query", {"query": delete_query})
