from contextvars import ContextVar

from intelligence_layer.core import InMemoryTaskSpan, InMemoryTracer

current_tracer_var: ContextVar[InMemoryTracer | None] = ContextVar(
    "current_tracer", default=None
)

root_task_span_var: ContextVar[InMemoryTaskSpan | None] = ContextVar(
    "root_task_span", default=None
)
