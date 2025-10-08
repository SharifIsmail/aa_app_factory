from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from starlette.applications import Starlette

user_last_seen: Gauge = Gauge(
    "usecase_user_last_seen_timestamp_seconds",
    "Last‐seen UNIX timestamp (UTC) per user",
    ["user_id"],
)


user_endpoint_requests: Counter = Counter(
    "usecase_user_endpoint_requests_total",
    "Total HTTP requests per user and endpoint",
    ["user_id", "endpoint"],
)


def with_metrics(app: Starlette) -> None:
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics"],
    )
    instrumentator.instrument(app)
    instrumentator.add(metrics.default())
    instrumentator.expose(
        app, endpoint="/metrics", include_in_schema=False, should_gzip=True
    )
