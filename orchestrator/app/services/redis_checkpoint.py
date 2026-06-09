import json
import os
from redis.asyncio import Redis
from ..models.contracts import AgentState


async def checkpoint_state(project_id: str, node_name: str, state: AgentState) -> None:
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return

    client = Redis.from_url(redis_url, decode_responses=True)
    try:
        key = f"checkpoint:{project_id}:{node_name}"
        await client.set(key, json.dumps(state.model_dump()))
        await client.rpush(f"checkpoints:{project_id}", key)
    finally:
        await client.aclose()

