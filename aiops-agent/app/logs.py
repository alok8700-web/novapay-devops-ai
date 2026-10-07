import re
from collections import Counter


LOG_PATTERN = re.compile(
    r"^(?P<method>\S+)\s+"
    r"(?P<path>\S+)\s+"
    r"(?P<status>\d{3})\s+"
    r"(?P<size>\S+)\s+-\s+"
    r"(?P<latency>[\d.]+)\s+ms$"
)


def analyze_logs(log_text: str) -> dict:
    requests = []
    invalid_lines = 0

    for line in log_text.splitlines():
        line = line.strip()

        if not line:
            continue

        match = LOG_PATTERN.match(line)

        if not match:
            invalid_lines += 1
            continue

        data = match.groupdict()

        requests.append({
            "method": data["method"],
            "path": data["path"],
            "status": int(data["status"]),
            "size": int(data["size"]) if data["size"].isdigit() else None,
            "latency_ms": float(data["latency"]),
        })

    status_counts = Counter(
        request["status"] // 100
        for request in requests
    )

    error_requests = [
        request
        for request in requests
        if request["status"] >= 400
    ]

    server_errors = [
        request
        for request in requests
        if request["status"] >= 500
    ]

    slow_requests = [
        request
        for request in requests
        if request["latency_ms"] > 1000
    ]

    total_requests = len(requests)

    error_rate = (
        len(error_requests) / total_requests * 100
        if total_requests
        else 0
    )

    average_latency = (
        sum(request["latency_ms"] for request in requests)
        / total_requests
        if total_requests
        else 0
    )

    endpoint_counts = Counter(
        request["path"]
        for request in error_requests
    )

    return {
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
    }
