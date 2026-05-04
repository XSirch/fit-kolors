from datetime import datetime, timezone
import os
from typing import Optional
from uuid import uuid4

import uvicorn
from analyzer import AnalysisProviderError, ColorAnalyzer
from config import API_VERSION
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import HttpUrl, TypeAdapter
from response_normalizer import normalize_analysis_response
from rq.job import Job

from jobs import get_analysis_queue, get_redis_connection, process_analysis_job
from schemas import ColorAnalysisResponse, WebhookJobAccepted


app = FastAPI(
    title="Fit-Kolors API",
    description="API RESTful para analise de colorimetria pessoal utilizando IA.",
    version=API_VERSION,
)


def get_allowed_origins():
    raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def get_api_keys():
    raw_keys = os.getenv("API_KEYS", "")
    return [key.strip() for key in raw_keys.split(",") if key.strip()]


def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    api_keys = get_api_keys()
    if not api_keys:
        raise HTTPException(status_code=503, detail="API authentication is not configured.")

    if not x_api_key or x_api_key not in api_keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

    return x_api_key


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


analyzer = ColorAnalyzer()
http_url_adapter = TypeAdapter(HttpUrl)
analysis_queue = get_analysis_queue()
redis_connection = get_redis_connection()


def validate_image_upload(file: UploadFile):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado deve ser uma imagem (jpeg, png).")


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "Fit-Kolors API",
        "endpoints": {
            "analysis": "/analyze [POST]",
            "analysis_webhook": "/analyze/webhook [POST]",
            "analysis_job": "/analysis/jobs/{job_id} [GET]",
            "docs": "/docs [GET]",
        },
        "allowed_origins": get_allowed_origins(),
    }


@app.post("/analyze", response_model=ColorAnalysisResponse, tags=["Analysis"])
async def analyze_image(
    file: UploadFile = File(...),
    _api_key: str = Depends(require_api_key),
):
    """
    Recebe uma imagem e retorna o dossie completo de colorimetria na mesma requisicao.
    """
    validate_image_upload(file)

    try:
        contents = await file.read()
        result = await analyzer.analyze_face(contents)
        return normalize_analysis_response(result)
    except AnalysisProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento: {str(e)}")


@app.post("/analyze/webhook", response_model=WebhookJobAccepted, status_code=202, tags=["Analysis"])
async def analyze_image_with_webhook(
    file: UploadFile = File(...),
    webhook_url: str = Form(...),
    webhook_secret: Optional[str] = Form(default=None),
    _api_key: str = Depends(require_api_key),
):
    """
    Recebe uma imagem, agenda a analise e envia o resultado por webhook ao concluir.
    """
    validate_image_upload(file)

    try:
        validated_url = str(http_url_adapter.validate_python(webhook_url))
    except Exception:
        raise HTTPException(status_code=400, detail="webhook_url deve ser uma URL HTTP/HTTPS valida.")

    contents = await file.read()
    job_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        job = analysis_queue.enqueue(
            process_analysis_job,
            kwargs={
                "job_id": job_id,
                "image_data": contents,
                "webhook_url": validated_url,
                "created_at": created_at,
                "webhook_secret": webhook_secret,
            },
            job_id=job_id,
            job_timeout="10m",
            result_ttl=86400,
            failure_ttl=86400,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Fila de analise indisponivel: {str(e)}")

    return {
        "job_id": job.id,
        "status": "queued",
        "queue": analysis_queue.name,
        "webhook_url": validated_url,
    }


@app.get("/analysis/jobs/{job_id}", tags=["Analysis"])
async def get_analysis_job(
    job_id: str,
    _api_key: str = Depends(require_api_key),
):
    try:
        job = Job.fetch(job_id, connection=redis_connection)
    except Exception:
        raise HTTPException(status_code=404, detail="Job nao encontrado ou Redis indisponivel.")

    payload = {
        "job_id": job.id,
        "status": job.get_status(refresh=True),
        "queue": analysis_queue.name,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "ended_at": job.ended_at.isoformat() if job.ended_at else None,
    }

    if job.is_finished:
        payload["event"] = job.result.get("event") if isinstance(job.result, dict) else None
        payload["error"] = job.result.get("error") if isinstance(job.result, dict) else None
    elif job.is_failed:
        payload["error"] = str(job.exc_info)

    return payload


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
