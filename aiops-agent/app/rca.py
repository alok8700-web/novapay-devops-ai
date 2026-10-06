def analyze_incident(health: dict, metrics: dict) -> dict:
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
            f"Health response time is {health['response_time_ms']} ms."
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

    return {
        "severity": severity,
        "probable_root_cause": probable_root_cause,
        "findings": findings,
        "recommendations": recommendations,
    }
