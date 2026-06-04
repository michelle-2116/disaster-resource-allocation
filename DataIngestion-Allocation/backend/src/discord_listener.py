"""
discord_listener.py - Standalone Discord bot listener.

Run with:
    python -m src.discord_listener
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import aiohttp
import discord
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("DISCORD_LISTENER")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _channel_ids() -> set[int]:
    raw = _required_env("DISCORD_CHANNEL_IDS")
    channel_ids = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            channel_ids.add(int(item))
        except ValueError as exc:
            raise RuntimeError(f"Invalid Discord channel ID: {item}") from exc
    if not channel_ids:
        raise RuntimeError("DISCORD_CHANNEL_IDS must include at least one channel ID")
    return channel_ids


def _attachment_payload(attachment: discord.Attachment) -> dict[str, Any]:
    return {
        "url": attachment.url,
        "filename": attachment.filename,
        "content_type": attachment.content_type,
        "size": attachment.size,
    }


def _message_payload(message: discord.Message) -> dict[str, Any]:
    channel_name = getattr(message.channel, "name", str(message.channel))
    return {
        "content": message.content,
        "username": str(message.author),
        "timestamp": message.created_at.isoformat(),
        "channel_id": str(message.channel.id),
        "channel_name": channel_name,
        "attachments": [_attachment_payload(item) for item in message.attachments],
    }


class DisasterDiscordClient(discord.Client):
    def __init__(
        self,
        channel_ids: set[int],
        backend_url: str,
        ingest_secret: str | None,
        retries: int,
        timeout_seconds: float,
    ) -> None:
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.channel_ids = channel_ids
        self.backend_url = backend_url
        self.ingest_secret = ingest_secret
        self.retries = max(1, retries)
        self.timeout_seconds = timeout_seconds
        self.session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        if self.session:
            await self.session.close()
        await super().close()

    async def on_ready(self) -> None:
        logger.info(
            "Discord listener ready as %s; listening to channels: %s",
            self.user,
            ", ".join(str(channel_id) for channel_id in sorted(self.channel_ids)),
        )

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            logger.debug("Ignoring bot message from %s", message.author)
            return

        if message.channel.id not in self.channel_ids:
            logger.debug("Ignoring message from unconfigured channel %s", message.channel.id)
            return

        payload = _message_payload(message)
        await self._send_to_backend(payload)

    async def _send_to_backend(self, payload: dict[str, Any]) -> None:
        if self.session is None:
            raise RuntimeError("HTTP session is not initialized")

        headers = {"Content-Type": "application/json"}
        if self.ingest_secret:
            headers["X-Discord-Ingest-Secret"] = self.ingest_secret

        for attempt in range(1, self.retries + 1):
            try:
                async with self.session.post(
                    self.backend_url,
                    json=payload,
                    headers=headers,
                ) as response:
                    body = await response.text()
                    if 200 <= response.status < 300:
                        logger.info(
                            "Forwarded Discord message from #%s; backend status=%s",
                            payload.get("channel_name"),
                            response.status,
                        )
                        return
                    if response.status < 500 and response.status != 429:
                        logger.error(
                            "Backend rejected Discord message with status=%s body=%s",
                            response.status,
                            body[:500],
                        )
                        return
                    logger.warning(
                        "Backend request failed attempt %d/%d status=%s body=%s",
                        attempt,
                        self.retries,
                        response.status,
                        body[:500],
                    )
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning(
                    "Backend request failed attempt %d/%d: %s",
                    attempt,
                    self.retries,
                    exc,
                )

            if attempt < self.retries:
                await asyncio.sleep(2 ** (attempt - 1))

        logger.error(
            "Failed to forward Discord message after %d attempt(s): channel=%s username=%s",
            self.retries,
            payload.get("channel_name"),
            payload.get("username"),
        )


def main() -> None:
    token = _required_env("DISCORD_BOT_TOKEN")
    channel_ids = _channel_ids()
    backend_url = os.getenv("DISCORD_BACKEND_URL", "http://127.0.0.1:8000/discord/messages")
    ingest_secret = os.getenv("DISCORD_INGEST_SECRET")
    retries = int(os.getenv("DISCORD_REQUEST_RETRIES", "3"))
    timeout_seconds = float(os.getenv("DISCORD_REQUEST_TIMEOUT_SECONDS", "10"))

    logger.info("Starting Discord listener for backend URL: %s", backend_url)
    client = DisasterDiscordClient(
        channel_ids=channel_ids,
        backend_url=backend_url,
        ingest_secret=ingest_secret,
        retries=retries,
        timeout_seconds=timeout_seconds,
    )
    client.run(token)


if __name__ == "__main__":
    main()
