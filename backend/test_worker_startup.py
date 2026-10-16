"""Run the actual startup against an isolated Redis, without executing jobs."""
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import time
from types import ModuleType
import unittest
from unittest.mock import patch
from uuid import uuid4

from redis import Redis
from rq import Queue, Worker
from rq.job import Job


@unittest.skipUnless(os.getenv("WORKER_TEST_REDIS_URL"), "isolated Redis required")
class WorkerStartupTests(unittest.TestCase):
    def setUp(self):
        self.url = os.environ["WORKER_TEST_REDIS_URL"]
        self.connection = Redis.from_url(self.url)
        namespace = "startup-test-" + uuid4().hex
        self.prefix = "fitkolors-" + namespace
        self.queue = Queue(namespace, connection=self.connection)
        self.jobs_module = ModuleType("jobs")
        self.jobs_module.REDIS_URL = self.url
        self.jobs_module.ANALYSIS_QUEUE = namespace

    def start(self, prefix):
        names = []

        def register_only(worker, *args, **kwargs):
            worker.register_birth()
            names.append(worker.name)

        environment = dict(os.environ)
        if prefix is None:
            environment.pop("WORKER_NAME", None)
        else:
            environment["WORKER_NAME"] = prefix
        with patch.dict(os.environ, environment, clear=True), patch.dict(sys.modules, {"jobs": self.jobs_module}), patch.object(Worker, "work", register_only):
            runpy.run_path(str(Path(__file__).with_name("worker.py")), run_name="__main__")
        return names[0]

    def test_stale_registration_does_not_delay_restart_or_change_jobs(self):
        old = Worker([self.queue], connection=self.connection, name=self.prefix)
        old.register_birth()
        self.connection.hset(old.key, "last_heartbeat", "2000-01-01T00:00:00.000000Z")
        job = self.queue.enqueue("json.dumps", {"fixture": True}, job_id=uuid4().hex)
        old_registration = self.connection.hgetall(old.key)
        job_data = self.connection.hgetall(job.key)
        queued = self.connection.lrange(self.queue.key, 0, -1)
        started = time.monotonic()

        new_name = self.start(self.prefix)

        self.assertLess(time.monotonic() - started, 5)
        self.assertNotEqual(new_name, old.name)
        self.assertTrue(new_name.startswith(self.prefix + "-"))
        self.assertGreater(self.connection.ttl(old.key), 300)
        self.assertEqual(self.connection.hgetall(old.key), old_registration)
        self.assertEqual(self.connection.hgetall(job.key), job_data)
        self.assertEqual(self.connection.lrange(self.queue.key, 0, -1), queued)

    def test_live_worker_and_its_active_job_are_not_reclaimed(self):
        old = Worker([self.queue], connection=self.connection, name=self.prefix)
        old.register_birth()
        job = Job.create("json.dumps", args=({"active_fixture": True},), connection=self.connection)
        job.set_status("started")
        job.save()
        self.connection.hset(old.key, mapping={"state": "busy", "current_job": job.id})
        registration = self.connection.hgetall(old.key)
        job_data = self.connection.hgetall(job.key)

        new_name = self.start(self.prefix)

        self.assertNotEqual(new_name, old.name)
        self.assertEqual(self.connection.hgetall(old.key), registration)
        self.assertEqual(self.connection.hgetall(job.key), job_data)

    def test_two_process_starts_with_same_prefix_get_distinct_identities(self):
        first = self.start(self.prefix)
        second = self.start(self.prefix)
        self.assertNotEqual(first, second)
        self.assertTrue(self.connection.exists("rq:worker:" + first))
        self.assertTrue(self.connection.exists("rq:worker:" + second))

    def test_unconfigured_name_keeps_rq_random_identity(self):
        self.assertNotEqual(self.start(None), self.start(None))

    def test_real_process_handles_queued_job_before_old_registration_expires(self):
        old = Worker([self.queue], connection=self.connection, name=self.prefix)
        old.register_birth()
        old_data = self.connection.hgetall(old.key)
        job = self.queue.enqueue("operator.add", 2, 3, job_id=uuid4().hex)
        environment = dict(os.environ, REDIS_URL=self.url, ANALYSIS_QUEUE=self.queue.name,
                           WORKER_NAME=self.prefix, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="/app")
        process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("worker.py"))],
                                   env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if job.is_finished or process.poll() is not None:
                    break
                time.sleep(0.1)
            self.assertTrue(job.is_finished, "worker did not resume the existing queue")
            self.assertEqual(job.return_value(), 5)
            self.assertEqual(self.queue.count, 0)
            self.assertGreater(self.connection.ttl(old.key), 300)
            self.assertEqual(self.connection.hgetall(old.key), old_data)
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
            process.communicate(timeout=15)


if __name__ == "__main__":
    unittest.main()
