import os

from fastapi import FastAPI
from pydantic import BaseModel

from app.health import check_service
from app.logs import analyze_logs
from app.metrics import fetch_metrics
from app.prometheus import (
    analyze_prometheus_metrics,
    calculate_window_delta,
)
from app.rca import analyze_incident


app = FastAPI(
    title="NovaPay AIOps Agent",
    version="0.4.0",
)


NOVAPAY_URL = os.getenv(
    "NOVAPAY_URL",
    "http://novapay:4000",
)

NOVAPAY_HEALTH_URL = f"{NOVAPAY_URL}/api/health"
NOVAPAY_METRICS_URL = f"{NOVAPAY_URL}/metrics"

# Previous Prometheus snapshot used for time-window analysis.
previous_prometheus_snapshot = None


class LogRequest(BaseModel):
    logs: str


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "novapay-aiops-agent",
        "version": "0.4.0",
    }


@app.get("/analyze")
async def analyze():
    health_result = await check_service(
        NOVAPAY_HEALTH_URL
    )

    metrics_result = await fetch_metrics(
        NOVAPAY_METRICS_URL
    )

    global previous_prometheus_snapshot

    prometheus_analysis = analyze_prometheus_metrics(
        metrics_result.get("metrics", "")
    )

    if previous_prometheus_snapshot is None:
        window_analysis = {
            "available": False,
            "reason": "Waiting for a previous Prometheus snapshot.",
        }
    else:
        window_analysis = {
            "available": True,
            **calculate_window_delta(
                previous_prometheus_snapshot,
                prometheus_analysis,
            ),
        }

    previous_prometheus_snapshot = prometheus_analysis

    analysis = analyze_incident(
        health_result,
        metrics_result,
        prometheus=prometheus_analysis,
        prometheus_window=window_analysis,
    )

    return {
        "service": "novapay",
        "health": health_result,
        "prometheus": prometheus_analysis,
        "prometheus_window": window_analysis,
        "analysis": analysis,
    }


@app.post("/logs/analyze")
async def analyze_application_logs(
    payload: LogRequest,
):
    log_analysis = analyze_logs(payload.logs)

    health_result = await check_service(
        NOVAPAY_HEALTH_URL
    )

    metrics_result = await fetch_metrics(
        NOVAPAY_METRICS_URL
    )

    prometheus_analysis = analyze_prometheus_metrics(
        metrics_result.get("metrics", "")
    )

    analysis = analyze_incident(
        health_result,
        metrics_result,
        log_analysis,
        prometheus_analysis,
    )

    return {
        "service": "novapay",
        "logs": log_analysis,
        "prometheus": prometheus_analysis,
        "analysis": analysis,
    }
