# Redis-backed store
import redis
from mcp.schemas import MCPContext
import json

class MCPContextStore:
    def __init__(self):
        self.redis = redis.Redis(
            host='redis',
            decode_responses=True
        )

    async def get(self) -> MCPContext:
        """Get the latest context"""
        key = f"mcp:context"
        data = self.redis.get(key)
        if data:
            return MCPContext(**json.loads(data))
        return MCPContext(user_query="")

    async def update(self, context: MCPContext):
        """Update context"""
        key = f"mcp:context"
        self.redis.set(key, context.json())
        self.redis.expire(key, 86400)  # TTL 24h