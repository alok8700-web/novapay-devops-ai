def analyze_incident(
    health: dict,
    metrics: dict,
    logs: dict | None = None,
) -> dict:
    findings = []
    severity = "LOW"
    probable_root_cause = "No immediate incident detected."
    recommendations = []

    if not health.get("healthy"):
        severity = "CRITICAL"
        probable_root_cause = "NovaPay health endpoint is unavailable."

        findings.append("NovaPay health check failed.")

        recommendations.extend([
            "Check application logs.",
            "Check container or pod status.",
            "Check recent deployment changes.",
            "Verify application dependencies.",
        ])

    elif health.get("response_time_ms", 0) > 1000:
        severity = "WARNING"
        probable_root_cause = "NovaPay response latency is elevated."

        findings.append(
            f"Health response time is "
            f"{health['response_time_ms']} ms."
        )

        recommendations.extend([
            "Inspect application CPU and memory usage.",
            "Review recent application changes.",
            "Check backend dependency latency.",
        ])

    if not metrics.get("healthy"):
        if severity != "CRITICAL":
            severity = "WARNING"

        findings.append("Prometheus metrics endpoint is unavailable.")

        recommendations.append(
            "Verify the application's /metrics endpoint."
        )

    if logs:
        server_errors = logs.get("server_error_requests", 0)
        client_errors = logs.get("client_error_requests", 0)
        slow_requests = logs.get("slow_request_count", 0)
        error_rate = logs.get("error_rate_percent", 0)

        if server_errors > 0:
            severity = "CRITICAL"

            findings.append(
                f"{server_errors} HTTP 5xx server error(s) detected."
            )

            probable_root_cause = (
                "NovaPay is experiencing server-side HTTP errors."
            )

            recommendations.extend([
                "Inspect application exception logs.",
                "Check application dependencies.",
                "Review recent deployments.",
            ])

        elif client_errors > 0:
            if severity == "LOW":
                severity = "WARNING"

            findings.append(
                f"{client_errors} HTTP 4xx client error(s) detected."
            )

            if severity != "CRITICAL":
                probable_root_cause = (
                    "NovaPay is receiving invalid or unsuccessful client requests."
                )

            recommendations.append(
                "Inspect affected API endpoints and request validation."
            )

        if slow_requests > 0:
            if severity == "LOW":
                severity = "WARNING"

            findings.append(
                f"{slow_requests} request(s) exceeded 1000 ms latency."
            )

            if severity != "CRITICAL":
                probable_root_cause = (
                    "NovaPay is experiencing elevated request latency."
                )

            recommendations.append(
                "Inspect application CPU, memory, and dependency latency."
            )

        if error_rate >= 10:
            if severity == "LOW":
                severity = "WARNING"

            findings.append(
                f"HTTP error rate is {error_rate}%."
            )

    return {
        "severity": severity,
        "probable_root_cause": probable_root_cause,
        "findings": findings,
        "recommendations": list(dict.fromkeys(recommendations)),
    }
