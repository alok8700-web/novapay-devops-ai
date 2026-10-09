import re
from collections import Counter


# Existing HTTP access-log format:
# GET /api/payments 200 512 - 45.5 ms
HTTP_LOG_PATTERN = re.compile(
    r"^(?P<method>\S+)\s+"
    r"(?P<path>\S+)\s+"
    r"(?P<status>\d{3})\s+"
    r"(?P<size>\S+)\s+-\s+"
    r"(?P<latency>[\d.]+)\s+ms$"
)

# Application logs may begin with an ISO timestamp, followed by
# a severity level and an optional service/logger name.
APP_LOG_PATTERN = re.compile(
    r"^(?:"
    r"\d{4}-\d{2}-\d{2}[T ]\S+\s+"
    r")?"
    r"(?:\[[^\]]+\]\s*)?"
    r"(?P<level>TRACE|DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)"
    r"\s*:?\s+"
    r"(?P<message>.*)$",
    re.IGNORECASE,
)

DATABASE_PATTERN = re.compile(
    r"database|db connection|connection pool|"
    r"connection timeout|connection refused|"
    r"too many connections|could not connect",
    re.IGNORECASE,
)


def analyze_logs(log_text: str) -> dict:
    requests = []
    invalid_lines = 0
    application_levels = Counter()
    application_errors = []
    database_errors = 0

    for raw_line in log_text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        # Prefer the original HTTP access-log parser.
        http_match = HTTP_LOG_PATTERN.match(line)

        if http_match:
            data = http_match.groupdict()

            requests.append({
                "method": data["method"],
                "path": data["path"],
                "status": int(data["status"]),
                "size": (
                    int(data["size"])
                    if data["size"].isdigit()
                    else None
                ),
                "latency_ms": float(data["latency"]),
            })
            continue

        # Otherwise try a structured/severity-based application log.
        app_match = APP_LOG_PATTERN.match(line)

        if not app_match:
            invalid_lines += 1
            continue

        level = app_match.group("level").upper()
        message = app_match.group("message").strip()

        if level == "WARN":
            level = "WARNING"

        application_levels[level] += 1

        if level in {"ERROR", "CRITICAL", "FATAL"}:
            application_errors.append({
                "level": level,
                "message": message[:500],
            })

            if DATABASE_PATTERN.search(message):
                database_errors += 1

    status_counts = Counter(
        request["status"] // 100
        for request in requests
    )

    error_requests = [
        request for request in requests
        if request["status"] >= 400
    ]

    server_errors = [
        request for request in requests
        if request["status"] >= 500
    ]

    slow_requests = [
        request for request in requests
        if request["latency_ms"] > 1000
    ]

    total_requests = len(requests)

    error_rate = (
        len(error_requests) / total_requests * 100
        if total_requests else 0
    )

    average_latency = (
        sum(request["latency_ms"] for request in requests)
        / total_requests
        if total_requests else 0
    )

    endpoint_counts = Counter(
        request["path"] for request in error_requests
    )

    return {
        # Existing HTTP access-log fields
        "total_requests": total_requests,
        "successful_requests": status_counts.get(2, 0),
        "redirect_requests": status_counts.get(3, 0),
        "client_error_requests": status_counts.get(4, 0),
        "server_error_requests": status_counts.get(5, 0),
        "error_rate_percent": round(error_rate, 2),
        "average_latency_ms": round(average_latency, 2),
        "slow_request_count": len(slow_requests),
        "affected_endpoints": dict(endpoint_counts),
        "invalid_log_lines": invalid_lines,

        # New application-log fields
        "application_log_count": sum(application_levels.values()),
        "application_log_levels": dict(application_levels),
        "application_error_count": len(application_errors),
        "application_critical_count": sum(
            application_levels[level]
            for level in ("CRITICAL", "FATAL")
        ),
        "database_error_count": database_errors,
        "application_errors": application_errors[:20],
    }
