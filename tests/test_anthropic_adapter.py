"""Tests para AnthropicAdapter."""

from datetime import datetime
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.infrastructure.ai.anthropic_adapter import AnthropicAdapter
from app.domain.entities import Message


def _mock_message_response(text: str):
    response = MagicMock()
    content_block = MagicMock()
    content_block.text = text
    response.content = [content_block]
    return response


@pytest.mark.asyncio
async def test_send_message_returns_text():
    adapter = AnthropicAdapter(api_key="sk-ant-dummy", system_prompt="be helpful")
    with patch.object(adapter.client.messages, "create",
                      new=AsyncMock(return_value=_mock_message_response("Hello!"))):
        reply = await adapter.send_message("Hi", [], "claude-haiku-4-5")
    assert reply == "Hello!"


@pytest.mark.asyncio
async def test_send_message_includes_history():
    """Verifica que el historial se transforma a roles user/assistant."""
    adapter = AnthropicAdapter(api_key="sk-ant-dummy", system_prompt="")
    history = [
        Message(id=1, conversation_id="c1", role="user", content="hola", created_at=datetime.now()),
        Message(id=2, conversation_id="c1", role="assistant", content="hey", created_at=datetime.now()),
    ]
    with patch.object(adapter.client.messages, "create",
                      new=AsyncMock(return_value=_mock_message_response("..."))) as mock:
        await adapter.send_message("siguiente", history, "claude-sonnet-4-6")
    call_kwargs = mock.call_args.kwargs
    msgs = call_kwargs["messages"]
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert msgs[2]["role"] == "user"
    assert msgs[2]["content"] == "siguiente"


@pytest.mark.asyncio
async def test_adapter_name():
    adapter = AnthropicAdapter(api_key="sk-ant-dummy", system_prompt="")
    assert adapter.name == "anthropic"
