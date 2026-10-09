from app.logs import analyze_logs


def test_successful_http_access_log():
    result = analyze_logs("GET /api/payments 200 512 - 45.5 ms")

    assert result["total_requests"] == 1
    assert result["successful_requests"] == 1
    assert result["server_error_requests"] == 0
    assert result["invalid_log_lines"] == 0


def test_http_500_and_slow_request():
    result = analyze_logs("POST /api/payments 500 128 - 1250 ms")

    assert result["total_requests"] == 1
    assert result["server_error_requests"] == 1
    assert result["error_rate_percent"] == 100.0
    assert result["slow_request_count"] == 1
    assert result["affected_endpoints"] == {"/api/payments": 1}


def test_application_and_database_errors():
    logs = """2026-10-09T10:50:00Z ERROR payment-service: payment transaction failed due to database connection timeout
2026-10-09T10:50:01Z ERROR payment-service: database connection pool exhausted
2026-10-09T10:50:02Z CRITICAL payment-service: payment processing unavailable"""

    result = analyze_logs(logs)

    assert result["invalid_log_lines"] == 0
    assert result["application_log_count"] == 3
    assert result["application_error_count"] == 3
    assert result["application_critical_count"] == 1
    assert result["database_error_count"] == 2


def test_mixed_http_and_application_logs():
    logs = """GET /api/payments 200 512 - 45.5 ms
2026-10-09T10:50:00Z ERROR payment-service: database connection timeout"""

    result = analyze_logs(logs)

    assert result["total_requests"] == 1
    assert result["successful_requests"] == 1
    assert result["application_error_count"] == 1
    assert result["database_error_count"] == 1
    assert result["invalid_log_lines"] == 0
