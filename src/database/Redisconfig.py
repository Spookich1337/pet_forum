import os
from dotenv import load_dotenv
from redis.asyncio import Redis
from broadcaster import Broadcast


load_dotenv()
JWT_REDIS = os.getenv("JWT_REDIS")
jwt_redis = Redis.from_url(JWT_REDIS, decode_responses=True)


WEBSOCKET_REDIS = os.getenv("WEBSOCKET_REDIS")
broadcast = Broadcast(WEBSOCKET_REDIS)


async def get_jwt_redis():
    return jwt_redis
