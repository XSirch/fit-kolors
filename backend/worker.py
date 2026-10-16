import os
from uuid import uuid4

from redis import Redis
from rq import SimpleWorker, Worker

from jobs import ANALYSIS_QUEUE, REDIS_URL


if __name__ == "__main__":
    connection = Redis.from_url(REDIS_URL)
    name_prefix = os.getenv("WORKER_NAME")
    # Keep deployment identity while avoiding registrations left by dead processes.
    worker_name = f"{name_prefix}-{uuid4().hex}" if name_prefix else None
    worker_class = SimpleWorker if os.name == "nt" else Worker
    worker = worker_class([ANALYSIS_QUEUE], connection=connection, name=worker_name)
    worker.work()
