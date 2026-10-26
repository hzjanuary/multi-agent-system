"""Committed event identity notifications; PostgreSQL remains authoritative."""

import json
from typing import Any

from redis.asyncio import Redis


async def publish_committed(redis_url: str, identity: dict[str, Any]) -> None:
    client = Redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
    try:
        await client.publish("maos:events", json.dumps(identity))
    finally:
        await client.aclose()
