import os
from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")


redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


async def get_redis():
    return redis_client