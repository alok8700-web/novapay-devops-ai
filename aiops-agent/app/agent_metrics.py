from prometheus_client import Counter


analysis_total = Counter(
    "aiops_analysis_total",
    "Total number of AIOps analyses performed.",
)

incident_total = Counter(
    "aiops_incident_total",
    "Total number of AIOps incidents detected.",
    ["severity"],
)
