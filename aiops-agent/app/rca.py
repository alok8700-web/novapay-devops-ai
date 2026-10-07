def analyze_incident(
    health: dict,
    metrics: dict,
    logs: dict | None = None,
    prometheus: dict | None = None,
    prometheus_window: dict | None = None,
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

    log_5xx = 0
    log_4xx = 0
    slow_requests = 0
    log_error_rate = 0
    affected_endpoints = {}

    if logs:
        log_5xx = logs.get(
            "server_error_requests",
            0,
        )

        log_4xx = logs.get(
            "client_error_requests",
            0,
        )

        slow_requests = logs.get(
            "slow_request_count",
            0,
        )

        log_error_rate = logs.get(
            "error_rate_percent",
            0,
        )

        affected_endpoints = logs.get(
            "affected_endpoints",
            {},
        )

        if log_5xx > 0:
            raise_severity("CRITICAL")

            findings.append(
                f"{log_5xx} HTTP 5xx server error(s) "
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

        elif log_4xx > 0:
            raise_severity("WARNING")

            findings.append(
                f"{log_4xx} HTTP 4xx client error(s) "
                "detected in application logs."
            )

            if severity != "CRITICAL":
                probable_root_cause = (
                    "NovaPay is receiving invalid or "
                    "unsuccessful client requests."
                )

            recommendations.append(
                "Inspect the affected API endpoints."
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

        if log_error_rate >= 10:
            raise_severity("WARNING")

            findings.append(
                f"Application log error rate is "
                f"{log_error_rate}%."
            )

    # ---------------------------------------------------------
    # 4. Prometheus metrics
    # ---------------------------------------------------------

    metric_5xx = 0
    metric_4xx = 0
    metric_error_rate = 0
    metric_source = "cumulative"

    if prometheus_window and prometheus_window.get("available"):
        metric_5xx = prometheus_window.get(
            "server_errors",
            0,
        )

        metric_4xx = prometheus_window.get(
            "client_errors",
            0,
        )

        metric_error_rate = prometheus_window.get(
            "error_rate_percent",
            0,
        )

        metric_source = "time-window"

    elif prometheus:
        metric_5xx = prometheus.get(
            "server_errors",
            0,
        )

        metric_4xx = prometheus.get(
            "client_errors",
            0,
        )

        metric_error_rate = prometheus.get(
            "error_rate_percent",
            0,
        )

    if metric_5xx > 0:
        raise_severity("CRITICAL")

        findings.append(
            f"Prometheus {metric_source} reports {metric_5xx} "
            "HTTP 5xx server error(s)."
        )

        probable_root_cause = (
            "Prometheus metrics indicate "
            "server-side API failures."
        )

        recommendations.extend([
            "Inspect application exception logs.",
            "Check application dependencies.",
            "Review recent deployments.",
        ])

    elif metric_4xx > 0:
        raise_severity("WARNING")

        findings.append(
            f"Prometheus {metric_source} reports {metric_4xx} "
            "HTTP 4xx client error(s)."
        )

        if severity != "CRITICAL":
            probable_root_cause = (
                "Prometheus metrics indicate "
                "client-side API errors."
            )

        recommendations.append(
            "Review request validation and client payloads."
        )

    if metric_error_rate >= 10:
        raise_severity("WARNING")

        findings.append(
            f"Prometheus {metric_source} HTTP error rate is "
            f"{metric_error_rate}%."
        )

    # ---------------------------------------------------------
    # 5. Cross-source correlation
    # ---------------------------------------------------------

    if logs and prometheus:

        # 5xx correlation
        if log_5xx > 0 and metric_5xx > 0:
            raise_severity("CRITICAL")

            findings.append(
                "Application logs and Prometheus metrics "
                "both report HTTP 5xx errors."
            )

            probable_root_cause = (
                "Correlated application logs and "
                "Prometheus metrics confirm server-side "
                "HTTP failures."
            )

            recommendations.extend([
                "Inspect the affected API endpoints.",
                "Review application exception logs.",
                "Check recent deployments and configuration changes.",
            ])

        # 4xx correlation
        elif log_4xx > 0 and metric_4xx > 0:
            raise_severity("WARNING")

            findings.append(
                "Application logs and Prometheus metrics "
                "both report HTTP 4xx errors."
            )

            probable_root_cause = (
                "Correlated application logs and "
                "Prometheus metrics confirm client-side "
                "API errors."
            )

            if affected_endpoints:
                endpoint_list = ", ".join(
                    affected_endpoints.keys()
                )

                findings.append(
                    f"Affected endpoints: {endpoint_list}."
                )

            recommendations.extend([
                "Inspect the affected API endpoints.",
                "Review request validation and client payloads.",
            ])

        # Slow request correlation
        if slow_requests > 0 and health.get("healthy"):
            findings.append(
                "Application logs detected slow requests "
                "while the health endpoint remains available."
            )

            if severity == "LOW":
                raise_severity("WARNING")

            recommendations.append(
                "Inspect application latency and backend dependencies."
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
        "affected_endpoints": affected_endpoints,
        "recommendations": recommendations,
    }
