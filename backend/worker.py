import os

from redis import Redis
from rq import SimpleWorker, Worker

from jobs import ANALYSIS_QUEUE, REDIS_URL


if __name__ == "__main__":
    connection = Redis.from_url(REDIS_URL)
    worker_name = os.getenv("WORKER_NAME")
    worker_class = SimpleWorker if os.name == "nt" else Worker
    worker = worker_class([ANALYSIS_QUEUE], connection=connection, name=worker_name)
    worker.work()
