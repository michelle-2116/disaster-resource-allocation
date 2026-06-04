"""
discord_adapter.py - Adapt Discord messages into verified incident reports.

This module keeps Discord-specific prompt shaping separate from the FastAPI
route and reuses the existing verified_news tool output format.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from google import genai
from google.genai import types

from .allocator_config import GEMINI_MODEL
from .tool_definitions import (
    execute_verified_news_tool,
    get_verified_news_tool_definition,
)

logger = logging.getLogger("DISCORD_ADAPTER")


SYSTEM_PROMPT = """You are a CRISIS ANALYST reviewing Discord volunteer messages.

Decide whether the message reports a real disaster, emergency, or urgent relief need.
If it does, call the verified_news tool once for each distinct incident.
If the message is not disaster-related, too vague, spam, or only casual discussion, do not call any tool.

Use only the Discord message context provided. Do not invent facts. Keep summaries concise and include that the source was Discord."""


def _attachment_context(attachments: list[dict[str, Any]]) -> str:
    if not attachments:
        return "None"

    lines = []
    for attachment in attachments:
        filename = attachment.get("filename", "unknown")
        content_type = attachment.get("content_type") or "unknown type"
        url = attachment.get("url") or "no url"
        size = attachment.get("size")
        size_text = f", {size} bytes" if size is not None else ""
        lines.append(f"- {filename} ({content_type}{size_text}): {url}")
    return "\n".join(lines)


def _build_prompt(payload: dict[str, Any]) -> str:
    attachments = payload.get("attachments") or []
    return f"""DISCORD MESSAGE REVIEW

Message content:
{payload.get("content") or "[no text content]"}

Message metadata:
- Username: {payload.get("username") or "unknown"}
- Timestamp: {payload.get("timestamp") or "unknown"}
- Channel: {payload.get("channel_name") or "unknown"} ({payload.get("channel_id") or "unknown"})
- Attachments:
{_attachment_context(attachments)}

TASK:
If this Discord message reports a disaster-related incident or urgent relief need, call verified_news.
Use an incident_id that starts with DISCORD_ and is stable for this message where possible.
Set severity on the 1-10 scale based only on the message content.
If location is unclear, use "Unknown" rather than guessing."""


def analyze_discord_message(payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    Convert one Discord message payload into the existing verified incident shape.

    Returns None when the model does not identify a disaster incident.
    """
    content = (payload.get("content") or "").strip()
    attachments = payload.get("attachments") or []
    if not content and not attachments:
        logger.info("Ignoring empty Discord message payload")
        return None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required to analyze Discord messages")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=_build_prompt(payload),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[get_verified_news_tool_definition()],
            temperature=0.3,
            max_output_tokens=2000,
        ),
    )

    if not response or not response.candidates:
        logger.warning("Gemini returned no candidates for Discord message")
        return None

    tool_calls = []
    for candidate in response.candidates:
        if not candidate.content or not candidate.content.parts:
            continue
        for part in candidate.content.parts:
            if getattr(part, "function_call", None):
                tool_calls.append(part.function_call)

    if not tool_calls:
        logger.info("Discord message was not classified as a disaster incident")
        return None

    reports = []
    for func_call in tool_calls:
        if func_call.name != "verified_news":
            logger.warning("Ignoring unexpected Discord adapter tool call: %s", func_call.name)
            continue
        reports.append(execute_verified_news_tool(dict(func_call.args)))

    if not reports:
        return None
    if len(reports) == 1:
        return reports[0]
    return {"incidents": reports}
