from app.logs import analyze_logs
from app.rca import analyze_incident


def run_rca(log_text=""):
    logs = analyze_logs(log_text) if log_text else None

    return analyze_incident(
        health={"healthy": True, "response_time_ms": 25},
        metrics={"healthy": True},
        logs=logs,
        prometheus={},
        prometheus_window={
            "available": True,
            "server_errors": 0,
            "client_errors": 0,
            "error_rate_percent": 0,
        },
    )


def test_no_incident_returns_low_severity():
    result = run_rca("GET /api/payments 200 512 - 45.5 ms")

    assert result["severity"] == "LOW"
    assert result["probable_root_cause"] == "No immediate incident detected."


def test_http_500_returns_critical_severity():
    result = run_rca("POST /api/payments 500 128 - 1250 ms")

    assert result["severity"] == "CRITICAL"
    assert any("5xx" in finding for finding in result["findings"])
    assert result["affected_endpoints"] == {"/api/payments": 1}


def test_database_failure_returns_critical_with_remediation():
    logs = """2026-10-09T10:50:00Z ERROR payment-service: payment transaction failed due to database connection timeout
2026-10-09T10:50:01Z ERROR payment-service: database connection pool exhausted
2026-10-09T10:50:02Z CRITICAL payment-service: payment processing unavailable"""

    result = run_rca(logs)

    assert result["severity"] == "CRITICAL"
    assert "database" in result["probable_root_cause"].lower()
    assert any("connection/pool-related" in finding for finding in result["findings"])
    assert any("connection-pool" in item for item in result["recommendations"])


def test_unhealthy_service_returns_critical():
    result = analyze_incident(
        health={"healthy": False},
        metrics={"healthy": True},
    )

    assert result["severity"] == "CRITICAL"
    assert "health endpoint" in result["probable_root_cause"].lower()
