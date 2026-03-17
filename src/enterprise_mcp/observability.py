"""Structured logging and OpenTelemetry observability."""

import time
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import StatusCode

# ---- Context variables ---------------------------------------------------- #

_request_id: ContextVar[str] = ContextVar("request_id", default="")
_tenant_id: ContextVar[str] = ContextVar("tenant_id", default="")

# ---- Metrics counters ----------------------------------------------------- #

_tool_call_counts: dict[str, int] = {}
_tool_call_errors: dict[str, int] = {}
_tool_call_latencies: dict[str, list[float]] = {}


def get_tool_metrics() -> dict[str, Any]:
    """Return current tool call metrics for health checks."""
    metrics: dict[str, Any] = {}
    for tool_name, count in _tool_call_counts.items():
        errors = _tool_call_errors.get(tool_name, 0)
        latencies = _tool_call_latencies.get(tool_name, [])
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0.0
        metrics[tool_name] = {
            "total_calls": count,
            "error_count": errors,
            "error_rate": errors / count if count > 0 else 0.0,
            "avg_latency_ms": round(avg_latency, 2),
            "p99_latency_ms": round(p99_latency, 2),
        }
    return metrics


# ---- Structlog setup ------------------------------------------------------ #


def add_context(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add context variables to every log entry."""
    req_id = _request_id.get()
    ten_id = _tenant_id.get()
    if req_id:
        event_dict["request_id"] = req_id
    if ten_id:
        event_dict["tenant_id"] = ten_id
    return event_dict


def setup_logging(log_level: str = "INFO", json_output: bool = True) -> None:
    """Configure structlog for JSON structured logging."""
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_context,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "") -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance."""
    return structlog.get_logger(name)  # type: ignore[return-value]


# ---- OpenTelemetry setup -------------------------------------------------- #

_tracer: trace.Tracer | None = None


def setup_tracing(
    service_name: str = "enterprise-mcp-server",
    service_version: str = "2.0.0",
    otlp_endpoint: str = "",
) -> trace.Tracer:
    """Initialize OpenTelemetry tracing."""
    global _tracer

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        except ImportError:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name, service_version)
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the configured tracer, initializing with defaults if needed."""
    global _tracer
    if _tracer is None:
        _tracer = setup_tracing()
    return _tracer


# ---- Tool call instrumentation -------------------------------------------- #


async def traced_tool_call(
    tool_name: str,
    handler: Callable[..., Any],
    **kwargs: Any,
) -> Any:
    """Execute a tool handler with tracing, logging, and metrics."""
    logger = get_logger("tool_call")
    tracer = get_tracer()

    start_time = time.monotonic()
    _tool_call_counts[tool_name] = _tool_call_counts.get(tool_name, 0) + 1

    with tracer.start_as_current_span(
        f"tool.{tool_name}",
        attributes={
            "tool.name": tool_name,
            "tool.args": str(list(kwargs.keys())),
            "tenant.id": _tenant_id.get(""),
        },
    ) as span:
        try:
            result = await handler(**kwargs)
            duration_ms = (time.monotonic() - start_time) * 1000

            _tool_call_latencies.setdefault(tool_name, []).append(duration_ms)
            # Keep only last 1000 latency samples
            if len(_tool_call_latencies[tool_name]) > 1000:
                _tool_call_latencies[tool_name] = _tool_call_latencies[tool_name][-1000:]

            span.set_attribute("tool.duration_ms", duration_ms)
            span.set_attribute("tool.success", True)
            span.set_status(StatusCode.OK)

            logger.info(
                "tool_call_success",
                tool_name=tool_name,
                duration_ms=round(duration_ms, 2),
                success=True,
            )
            return result

        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            _tool_call_errors[tool_name] = _tool_call_errors.get(tool_name, 0) + 1
            _tool_call_latencies.setdefault(tool_name, []).append(duration_ms)

            span.set_attribute("tool.duration_ms", duration_ms)
            span.set_attribute("tool.success", False)
            span.set_attribute("tool.error_type", type(exc).__name__)
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)

            logger.error(
                "tool_call_error",
                tool_name=tool_name,
                duration_ms=round(duration_ms, 2),
                success=False,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            raise
