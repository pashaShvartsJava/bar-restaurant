from fastapi import HTTPException
from redis.asyncio import Redis

from ..redis.redis_client import redis


async def check_login_rate_limit(email: str):
    key = f"login_attempts:{email}"
    attempts = await redis.incr(key)
    if attempts == 1:
        await redis.expire(key, 60)
    if attempts > 5:
        raise HTTPException(status_code=429, detail="Слишком много попыток входа. Попробуйте позже.")

async def reset_login_rate_limit(email: str):
    key = f"login_attempts:{email}"
    await redis.delete(key)