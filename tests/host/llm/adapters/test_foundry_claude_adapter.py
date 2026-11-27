"""Unit tests for the Foundry Claude adapter's mapping helpers (no network, no API key).

Responses are built by hand as SDK Message objects, the shape the Anthropic API returns.
"""

from anthropic.types import Message

from claims_mcp.host.llm.adapters.foundry_claude_adapter import (
    build_anthropic_messages,
    build_anthropic_tool,
    build_model_turn,
)
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.llm.models.tool_spec import ToolSpec


def build_message(content_blocks: list[dict], stop_reason: str) -> Message:
    """Return an assistant Message holding the given raw content blocks and stop reason."""
    return Message.model_validate(
        {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-5-5-fast",
            "content": content_blocks,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


def test_build_anthropic_tool_maps_name_description_and_schema():
    """A ToolSpec becomes the Anthropic tool dict: name, description and input_schema as given."""
    employee_id_schema = {
        "type": "object",
        "properties": {"employee_id": {"type": "string"}},
        "required": ["employee_id"],
    }
    tool_spec = ToolSpec(
        name="get_employee_info",
        description="Use first for every request.",
        input_schema=employee_id_schema,
    )

    anthropic_tool = build_anthropic_tool(tool_spec)

    assert anthropic_tool == {
        "name": "get_employee_info",
        "description": "Use first for every request.",
        "input_schema": employee_id_schema,
    }


def test_build_model_turn_tool_use_response_returns_thought_and_tool_call():
    """Thinking summary + text before a tool_use become the thought; the call becomes a ToolCall."""
    message = build_message(
        [
            {"type": "thinking", "thinking": "Need the employee first.", "signature": "sig"},
            {"type": "text", "text": "I'll look up E001."},
            {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "get_employee_info",
                "input": {"employee_id": "E001"},
            },
        ],
        stop_reason="tool_use",
    )

    model_turn = build_model_turn(message)

    assert model_turn.thought_text == "Need the employee first.\nI'll look up E001."
    assert model_turn.tool_calls == [
        ToolCall(id="toolu_1", name="get_employee_info", arguments={"employee_id": "E001"})
    ]
    assert model_turn.final_text is None


def test_build_model_turn_text_only_response_returns_final_text():
    """A response with no tool_use is the final answer: its text is final_text, no tool calls."""
    message = build_message(
        [{"type": "text", "text": "Approved under ELG-2 (POL-STD-MONITOR)."}],
        stop_reason="end_turn",
    )

    model_turn = build_model_turn(message)

    assert model_turn.final_text == "Approved under ELG-2 (POL-STD-MONITOR)."
    assert model_turn.tool_calls == []


def test_build_model_turn_keeps_raw_blocks_as_provider_content():
    """The thinking block, signature included, is kept as raw provider_content for replay."""
    message = build_message(
        [
            {"type": "thinking", "thinking": "Check eligibility.", "signature": "sig-abc"},
            {"type": "text", "text": "Done."},
        ],
        stop_reason="end_turn",
    )

    model_turn = build_model_turn(message)

    thinking_blocks = [
        block for block in model_turn.provider_content if block["type"] == "thinking"
    ]
    assert thinking_blocks == [
        {"type": "thinking", "thinking": "Check eligibility.", "signature": "sig-abc"}
    ]


def test_build_anthropic_messages_replays_model_turn_content_unchanged():
    """An assistant turn goes back to Claude as exactly its provider_content, thinking included."""
    conversation = Conversation.start("You handle IT requests.", "E001 wants a monitor", [])
    model_turn = build_model_turn(
        build_message(
            [
                {"type": "thinking", "thinking": "Look up E001.", "signature": "sig-xyz"},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "get_employee_info",
                    "input": {"employee_id": "E001"},
                },
            ],
            stop_reason="tool_use",
        )
    )
    conversation.add_model_turn(model_turn)

    anthropic_messages = build_anthropic_messages(conversation)

    assistant_messages = [
        message for message in anthropic_messages if message["role"] == "assistant"
    ]
    assert assistant_messages == [{"role": "assistant", "content": model_turn.provider_content}]


def test_build_anthropic_messages_tool_results_become_one_user_message():
    """Two tool results go back as one user message with two tool_result blocks, by tool_use_id."""
    conversation = Conversation.start("You handle IT requests.", "Check E001 and E999", [])
    conversation.add_tool_results(
        [
            ToolResult(tool_call_id="toolu_1", content='{"role": "standard"}', is_error=False),
            ToolResult(tool_call_id="toolu_2", content="No employee with ID E999", is_error=True),
        ]
    )

    anthropic_messages = build_anthropic_messages(conversation)

    tool_result_messages = [
        message for message in anthropic_messages if isinstance(message["content"], list)
    ]
    assert tool_result_messages == [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_1",
                    "content": '{"role": "standard"}',
                    "is_error": False,
                },
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_2",
                    "content": "No employee with ID E999",
                    "is_error": True,
                },
            ],
        }
    ]
