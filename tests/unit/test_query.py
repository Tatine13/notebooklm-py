"""Tests for query functionality."""

import pytest
from unittest.mock import AsyncMock, patch
import json

from notebooklm.services.query import QueryResult, ConversationTurn
from notebooklm.api_client import NotebookLMClient
from notebooklm.auth import AuthTokens


@pytest.fixture
def auth_tokens():
    return AuthTokens(
        cookies={"SID": "test"},
        csrf_token="test_csrf",
        session_id="test_session",
    )


class TestQuery:
    @pytest.mark.asyncio
    async def test_query_new_conversation(self, auth_tokens, httpx_mock):
        import re
        # Mock query response (streaming chunks)
        # Format:
        # )]}'
        # <length>
        # [[["wrb.fr", null, "<inner_json>"]]]

        inner_json = json.dumps(
            [
                [
                    "This is the answer. It is now long enough to be valid.",
                    None,
                    None,
                    None,
                    [1],
                ]
            ]
        )
        chunk_json = json.dumps([["wrb.fr", None, inner_json]])

        response_body = f")]}}'\n{len(chunk_json)}\n{chunk_json}\n"

        httpx_mock.add_response(
            url=re.compile(r".*GenerateFreeFormStreamed.*"),
            content=response_body.encode(),
            method="POST",
        )

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.query(
                notebook_id="nb_123",
                query_text="What is this?",
                source_ids=["test_source"],
            )

        assert (
            result["answer"] == "This is the answer. It is now long enough to be valid."
        )
        assert result["is_follow_up"] is False
        assert result["turn_number"] == 1

    @pytest.mark.asyncio
    async def test_query_follow_up(self, auth_tokens, httpx_mock):
        inner_json = json.dumps(
            [
                [
                    "Follow-up answer. This also needs to be longer than twenty characters.",
                    None,
                    None,
                    None,
                    [1],
                ]
            ]
        )
        chunk_json = json.dumps([["wrb.fr", None, inner_json]])
        response_body = f")]}}'\n{len(chunk_json)}\n{chunk_json}\n"

        httpx_mock.add_response(content=response_body.encode(), method="POST")

        async with NotebookLMClient(auth_tokens) as client:
            # Seed cache
            client._conversation_cache["conv_123"] = [
                {"query": "Q1", "answer": "A1", "turn_number": 1}
            ]

            result = await client.query(
                notebook_id="nb_123",
                query_text="Follow up?",
                conversation_id="conv_123",
                source_ids=["test_source"],
            )

        assert (
            result["answer"]
            == "Follow-up answer. This also needs to be longer than twenty characters."
        )
        assert result["is_follow_up"] is True
        assert result["turn_number"] == 2
