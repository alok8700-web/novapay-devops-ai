import re


METRIC_PATTERN = re.compile(
    r'^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)'
    r'(?:\{(?P<labels>[^}]*)\})?\s+'
    r'(?P<value>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)$'
)


def parse_labels(label_text=None):
    if not label_text:
        return {}

    labels = {}

    for key, value in re.findall(
        r'(\w+)="([^"]*)"',
        label_text,
    ):
        labels[key] = value

    return labels


def analyze_prometheus_metrics(metrics_text):
    request_metrics = []
    business_metrics = {}
    invalid_lines = 0

    for line in metrics_text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        match = METRIC_PATTERN.match(line)

        if not match:
            invalid_lines += 1
            continue

        name = match.group("name")
        labels = parse_labels(match.group("labels"))
        value = float(match.group("value"))

        if name == "novapay_http_requests_total":
            request_metrics.append({
                "method": labels.get("method"),
                "route": labels.get("route"),
                "status": (
                    int(labels["status"])
                    if labels.get("status", "").isdigit()
                    else None
                ),
                "value": value,
            })

        elif name in {
            "novapay_login_success_total",
            "novapay_login_failed_total",
            "novapay_transfer_total",
        }:
            business_metrics[name] = value

    total_requests = sum(
        metric["value"]
        for metric in request_metrics
    )

    error_requests = sum(
        metric["value"]
        for metric in request_metrics
        if metric["status"] is not None
        and metric["status"] >= 400
    )

    server_errors = sum(
        metric["value"]
        for metric in request_metrics
        if metric["status"] is not None
        and metric["status"] >= 500
    )

    client_errors = sum(
        metric["value"]
        for metric in request_metrics
        if metric["status"] is not None
        and 400 <= metric["status"] < 500
    )

    error_rate = (
        error_requests / total_requests * 100
        if total_requests
        else 0
    )

    return {
        "total_requests": int(total_requests),
        "error_requests": int(error_requests),
        "client_errors": int(client_errors),
        "server_errors": int(server_errors),
        "error_rate_percent": round(error_rate, 2),
        "business_metrics": business_metrics,
        "invalid_metric_lines": invalid_lines,
    }
