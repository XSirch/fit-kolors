import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from redis import Redis
from rq import Queue

from analyzer import ColorAnalyzer
from response_normalizer import normalize_analysis_response


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ANALYSIS_QUEUE = os.getenv("ANALYSIS_QUEUE", "analysis")


def get_redis_connection():
    return Redis.from_url(REDIS_URL)


def get_analysis_queue():
    return Queue(ANALYSIS_QUEUE, connection=get_redis_connection())


def deliver_webhook(webhook_url: str, payload: dict, webhook_secret: Optional[str] = None):
    headers = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["X-Fit-Kolors-Webhook-Secret"] = webhook_secret

    last_error = None
    for attempt in range(1, 4):
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(webhook_url, json=payload, headers=headers)
                response.raise_for_status()
            print(f"[Webhook] Job {payload['job_id']} entregue com sucesso.")
            return True
        except Exception as e:
            last_error = e
            print(f"[Webhook] Falha ao entregar job {payload['job_id']} (tentativa {attempt}/3): {e}")

    print(f"[Webhook] Entrega final falhou para job {payload['job_id']}: {last_error}")
    return False


def process_analysis_job(
    job_id: str,
    image_data: bytes,
    webhook_url: str,
    created_at: str,
    webhook_secret: Optional[str] = None,
):
    analyzer = ColorAnalyzer()

    try:
        result = _run_analysis(analyzer, image_data)
        payload = {
            "event": "analysis.completed",
            "job_id": job_id,
            "status": "completed",
            "created_at": created_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "error": None,
        }
    except Exception as e:
        payload = {
            "event": "analysis.failed",
            "job_id": job_id,
            "status": "failed",
            "created_at": created_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": str(e),
        }

    deliver_webhook(webhook_url, payload, webhook_secret)
    return payload


def _run_analysis(analyzer: ColorAnalyzer, image_data: bytes):
    import asyncio

    return normalize_analysis_response(asyncio.run(analyzer.analyze_face(image_data)))
