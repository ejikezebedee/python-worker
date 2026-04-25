from __future__ import annotations

import os

from dotenv import load_dotenv
from redis import Redis
from rq import Queue

load_dotenv()


def get_redis_connection() -> Redis:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url)


def get_default_queue() -> Queue:
    return Queue("opint-default", connection=get_redis_connection())
