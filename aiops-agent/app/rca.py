def analyze_incident(
    health: dict,
    metrics: dict,
    logs: dict | None = None,
    prometheus: dict | None = None,
) -> dict:
    findings = []
    recommendations = []

    severity = "LOW"
    probable_root_cause = "No immediate incident detected."

    def raise_severity(new_severity):
        nonlocal severity

        priority = {
            "LOW": 0,
            "WARNING": 1,
            "CRITICAL": 2,
        }

        if priority[new_severity] > priority[severity]:
            severity = new_severity

    # ---------------------------------------------------------
    # 1. Application health
    # ---------------------------------------------------------

    if not health.get("healthy"):
        raise_severity("CRITICAL")

        findings.append(
            "NovaPay health check failed."
        )

        probable_root_cause = (
            "NovaPay health endpoint is unavailable."
        )

        recommendations.extend([
            "Check application logs.",
            "Check container or pod status.",
            "Check recent deployment changes.",
            "Verify application dependencies.",
        ])

    elif health.get("response_time_ms", 0) > 1000:
        raise_severity("WARNING")

        findings.append(
            f"Health response time is "
            f"{health['response_time_ms']} ms."
        )

        probable_root_cause = (
            "NovaPay response latency is elevated."
        )

        recommendations.extend([
            "Inspect application CPU and memory usage.",
            "Review recent application changes.",
            "Check backend dependency latency.",
        ])

    # ---------------------------------------------------------
    # 2. Metrics endpoint
    # ---------------------------------------------------------

    if not metrics.get("healthy"):
        raise_severity("WARNING")

        findings.append(
            "Prometheus metrics endpoint is unavailable."
        )

        recommendations.append(
            "Verify the application's /metrics endpoint."
        )

    # ---------------------------------------------------------
    # 3. Application logs
    # ---------------------------------------------------------

    if logs:
        server_errors = logs.get(
            "server_error_requests",
            0,
        )

        client_errors = logs.get(
            "client_error_requests",
            0,
        )

        slow_requests = logs.get(
            "slow_request_count",
            0,
        )

        error_rate = logs.get(
            "error_rate_percent",
            0,
        )

        if server_errors > 0:
            raise_severity("CRITICAL")

            findings.append(
                f"{server_errors} HTTP 5xx server error(s) "
                "detected in application logs."
            )

            probable_root_cause = (
                "NovaPay is experiencing server-side "
                "HTTP errors."
            )

            recommendations.extend([
                "Inspect application exception logs.",
                "Check application dependencies.",
                "Review recent deployments.",
            ])

        elif client_errors > 0:
            raise_severity("WARNING")

            findings.append(
                f"{client_errors} HTTP 4xx client error(s) "
                "detected in application logs."
            )

            if severity != "CRITICAL":
                probable_root_cause = (
                    "NovaPay is receiving invalid or "
                    "unsuccessful client requests."
                )

            recommendations.append(
                "Inspect affected API endpoints and "
                "request validation."
            )

        if slow_requests > 0:
            raise_severity("WARNING")

            findings.append(
                f"{slow_requests} request(s) exceeded "
                "1000 ms latency."
            )

            if severity != "CRITICAL":
                probable_root_cause = (
                    "NovaPay is experiencing elevated "
                    "request latency."
                )

            recommendations.append(
                "Inspect application CPU, memory, and "
                "dependency latency."
            )

        if error_rate >= 10:
            raise_severity("WARNING")

            findings.append(
                f"HTTP error rate is {error_rate}%."
            )

    # ---------------------------------------------------------
    # 4. Prometheus metrics correlation
    # ---------------------------------------------------------

    if prometheus:
        prometheus_server_errors = prometheus.get(
            "server_errors",
            0,
        )

        prometheus_client_errors = prometheus.get(
            "client_errors",
            0,
        )

        prometheus_error_rate = prometheus.get(
            "error_rate_percent",
            0,
        )

        if prometheus_server_errors > 0:
            raise_severity("CRITICAL")

            findings.append(
                f"Prometheus reports "
                f"{prometheus_server_errors} HTTP 5xx "
                "server error(s)."
            )

            probable_root_cause = (
                "Prometheus metrics and application "
                "telemetry indicate server-side failures."
            )

            recommendations.extend([
                "Inspect application exception logs.",
                "Check application dependencies.",
                "Review recent deployments.",
            ])

        elif prometheus_client_errors > 0:
            raise_severity("WARNING")

            findings.append(
                f"Prometheus reports "
                f"{prometheus_client_errors} HTTP 4xx "
                "client error(s)."
            )

            if severity != "CRITICAL":
                probable_root_cause = (
                    "Prometheus metrics indicate "
                    "client-side API errors."
                )

            recommendations.append(
                "Inspect endpoints generating HTTP 4xx responses."
            )

        if prometheus_error_rate >= 10:
            raise_severity("WARNING")

            findings.append(
                f"Prometheus HTTP error rate is "
                f"{prometheus_error_rate}%."
            )

    # ---------------------------------------------------------
    # 5. Correlation
    # ---------------------------------------------------------

    if logs and prometheus:
        log_5xx = logs.get(
            "server_error_requests",
            0,
        )

        metric_5xx = prometheus.get(
            "server_errors",
            0,
        )

        log_4xx = logs.get(
            "client_error_requests",
            0,
        )

        metric_4xx = prometheus.get(
            "client_errors",
            0,
        )

        if log_5xx > 0 and metric_5xx > 0:
            raise_severity("CRITICAL")

            probable_root_cause = (
                "Correlated application logs and "
                "Prometheus metrics confirm server-side "
                "HTTP failures."
            )

            findings.append(
                "Application logs and Prometheus metrics "
                "both report HTTP 5xx errors."
            )

        elif log_4xx > 0 and metric_4xx > 0:
            raise_severity("WARNING")

            probable_root_cause = (
                "Correlated application logs and "
                "Prometheus metrics confirm client-side "
                "HTTP errors."
            )

            findings.append(
                "Application logs and Prometheus metrics "
                "both report HTTP 4xx errors."
            )

    # ---------------------------------------------------------
    # 6. Final recommendations
    # ---------------------------------------------------------

    recommendations = list(
        dict.fromkeys(recommendations)
    )

    return {
        "severity": severity,
        "probable_root_cause": probable_root_cause,
        "findings": findings,
        "recommendations": recommendations,
    }
