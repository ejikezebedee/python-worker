from rq import Worker, Queue, Connection
from redis import Redis
from utils.redis_queue import get_redis_connection


def main() -> None:
    redis_conn: Redis = get_redis_connection()
    with Connection(redis_conn):
        worker = Worker([Queue("opint-default")])
        worker.work()


if __name__ == "__main__":
    main()
