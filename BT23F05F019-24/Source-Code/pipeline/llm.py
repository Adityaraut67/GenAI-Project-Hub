"""Thin wrapper for schema-constrained model calls.

Every stage of the pipeline needs the same thing: send a screenshot plus some
instructions, get back a dict matching a known JSON schema. We get that by
declaring a tool and forcing the model to call it, which is more reliable than
asking for JSON in prose and parsing it.
"""

from __future__ import annotations

import json
import os
from typing import Any

from config import MAX_TOKENS, MODEL, TEMPERATURE, get_client


class ModelCallError(RuntimeError):
    """The model returned no usable tool call."""


def call_tool(
    *,
    system: str,
    content: list[dict[str, Any]],
    tool: dict[str, Any],
    max_tokens: int = MAX_TOKENS,
) -> dict[str, Any]:
    """Force a single call to `tool` and return its input payload.

    Supports Anthropic or Groq based on available API configuration.
    """
    client = get_client()

    # --- Groq (OpenAI-compatible) execution path ---
    if os.getenv("GROQ_API_KEY"):
        # Format user content into OpenAI / Groq standard message blocks
        groq_messages = []
        if system:
            groq_messages.append({"role": "system", "content": system})

        openai_content = []
        for block in content:
            if block.get("type") == "image":
                b64 = block["source"]["data"]
                media_type = block["source"].get("media_type", "image/png")
                openai_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{b64}"},
                })
            elif block.get("type") == "text":
                openai_content.append({"type": "text", "text": block.get("text", "")})
            else:
                openai_content.append(block)

        groq_messages.append({"role": "user", "content": openai_content})

        # Convert tool schema to standard OpenAI / Groq function definition
        fn_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {}),
            },
        }

        response = client.chat.completions.create(
            model=MODEL,
            max_completion_tokens=max_tokens,
            temperature=TEMPERATURE,
            messages=groq_messages,
            tools=[fn_tool],
            tool_choice={"type": "function", "function": {"name": tool["name"]}},
        )

        choice = response.choices[0]
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                if tc.function.name == tool["name"]:
                    args = tc.function.arguments
                    return json.loads(args) if isinstance(args, str) else args

        raise ModelCallError(
            f"Groq Model did not call {tool['name']!r}; finish_reason={choice.finish_reason}"
        )

    # --- Anthropic native execution path ---
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=TEMPERATURE,
        system=system,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": content}],
    )

    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == tool["name"]:
            return dict(block.input)

    raise ModelCallError(
        f"Model did not call {tool['name']!r}; stop_reason={response.stop_reason}"
    )
