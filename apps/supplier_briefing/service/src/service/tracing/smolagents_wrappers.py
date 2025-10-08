import json
from dataclasses import asdict
from inspect import signature
from typing import Any, Callable, Mapping

from intelligence_layer.connectors import StudioClient
from intelligence_layer.core import (
    InMemoryTaskSpan,
    InMemoryTracer,
    PydanticSerializable,
)
from loguru import logger
from smolagents import ChatMessage

from service.tracing.tracing_context import (
    current_tracer_var,
    root_task_span_var,
)


def extract_arguments(
    method: Callable[..., Any], *args: Any, **kwargs: Any
) -> dict[str, Any]:
    method_signature = signature(method)
    bound_args = method_signature.bind(*args, **kwargs)
    bound_args.apply_defaults()
    return bound_args.arguments


def strip_method_self(arguments: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in arguments.items() if key not in ("self", "cls")
    }


def safe_json_serialize(obj: Any) -> Any:
    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, dict):
        return {key: safe_json_serialize(value) for key, value in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [safe_json_serialize(item) for item in obj]

    if hasattr(obj, "__dict__"):
        try:
            return {
                key: safe_json_serialize(value)
                for key, value in obj.__dict__.items()
                if not key.startswith("_")  # Skip private attributes
            }
        except Exception:
            pass

    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return str(obj)


def get_input_data(
    method: Callable[..., Any], *args: Any, **kwargs: Any
) -> PydanticSerializable:
    arguments = extract_arguments(method, *args, **kwargs)
    stripped = strip_method_self(arguments)
    return safe_json_serialize(stripped)


def extract_smolagent_attributes(
    agent: Any, arguments: dict[str, Any]
) -> dict[str, Any]:
    attributes = {}

    if task := getattr(agent, "task", None):
        attributes["smolagents_task"] = task

    if additional_args := arguments.get("additional_args"):
        attributes["smolagents_additional_args"] = additional_args

    if max_steps := getattr(agent, "max_steps", None):
        attributes["smolagents_max_steps"] = max_steps

    if tools := getattr(agent, "tools", {}):
        attributes["smolagents_tools_names"] = list(tools.keys())

    if managed_agents := getattr(agent, "managed_agents", {}):
        managed_agents_info = []
        for managed_agent in managed_agents.values():
            agent_info = {
                "name": getattr(managed_agent, "name", None),
                "description": getattr(managed_agent, "description", None),
            }
            if additional_prompting := getattr(
                managed_agent, "additional_prompting", None
            ):
                agent_info["additional_prompting"] = additional_prompting
            elif managed_agent_prompt := getattr(
                managed_agent, "managed_agent_prompt", None
            ):
                agent_info["managed_agent_prompt"] = managed_agent_prompt

            if agent_obj := getattr(managed_agent, "agent", None):
                agent_info["max_steps"] = getattr(agent_obj, "max_steps", None)
                agent_info["tools_names"] = list(getattr(agent_obj, "tools", {}).keys())

            managed_agents_info.append(agent_info)
        attributes["smolagents_managed_agents"] = managed_agents_info

    return safe_json_serialize(attributes)


class RunWrapper:
    def __init__(self, studio_client: StudioClient) -> None:
        self.studio_client = studio_client

    def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        span_name = f"{instance.__class__.__name__}.run"
        agent = instance
        arguments = extract_arguments(wrapped, *args, **kwargs)

        input_data = get_input_data(wrapped, *args, **kwargs)
        if isinstance(input_data, dict):
            smolagent_attrs = extract_smolagent_attributes(agent, arguments)
            input_data.update(smolagent_attrs)

        tracer = InMemoryTracer()
        agent_output = None

        with tracer.task_span(task_name=span_name, input=input_data) as root_span:
            tracer_token = current_tracer_var.set(tracer)
            root_span_token = root_task_span_var.set(root_span)
            try:
                agent_output = wrapped(*args, **kwargs)
                root_span.record_output({"result": str(agent_output)})
            except Exception as e:
                root_span.log(
                    "Error during agent run execution",
                    {
                        "error_type": e.__class__.__name__,
                        "error_message": str(e),
                        "severity": "error",
                    },
                )
            finally:
                root_task_span_var.reset(root_span_token)
                current_tracer_var.reset(tracer_token)

        logger.info("Submitting agent run trace to Studio")
        self.studio_client.submit_from_tracer(tracer)
        tracer.entries = []
        logger.info("Agent run trace submitted successfully")
        return agent_output


class StepStreamWrapper:
    def __init__(self) -> None:
        pass

    def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        span_name = f"Step Stream {getattr(instance, 'step_number', 'Unknown')}"

        root_span = root_task_span_var.get()
        assert root_span is not None and isinstance(root_span, InMemoryTaskSpan), (
            "Tracing context missing root task span for StepStreamWrapper"
        )
        with root_span.task_span(task_name=span_name, input={}) as span:
            try:
                events: dict[str, dict[str, Any]] = {}
                for event in wrapped(*args, **kwargs):
                    events[f"{len(events)}_{event.__class__.__name__}"] = asdict(event)
                    yield event
                span.record_output({"events": events})
            except Exception as e:
                span.log("Error", {"error": str(e)})
                raise


class ModelWrapper:
    def __init__(self) -> None:
        pass

    def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        span_name = f"{instance.__class__.__name__}.generate"
        input_data = get_input_data(wrapped, *args, **kwargs)

        # TODO: using messages directly crashes the serialization
        # messages = cast(list[ChatMessage], input_data["messages"])  # type: ignore
        # input_data = {"messages": messages}
        input_data = {}

        root_span = root_task_span_var.get()
        assert root_span is not None and isinstance(root_span, InMemoryTaskSpan), (
            "Tracing context missing root task span for ModelWrapper"
        )
        with root_span.task_span(task_name=span_name, input=input_data) as span:
            try:
                output_message: ChatMessage = wrapped(*args, **kwargs)

                output_data = {
                    "role": output_message.role,
                    "content": output_message.content,
                }

                span.record_output(output_data)
                return output_message
            except Exception as e:
                span.log(
                    "Error during model generation",
                    {
                        "error_type": e.__class__.__name__,
                        "error_message": str(e),
                        "severity": "error",
                    },
                )
                raise


class ToolCallWrapper:
    def __init__(self) -> None:
        pass

    def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        tool = instance
        span_name = getattr(tool, "name", tool.__class__.__name__)

        input_data = get_input_data(wrapped, *args, **kwargs)

        if tool_name := getattr(tool, "name", None):
            input_data["tool_name"] = tool_name  # type: ignore

        if tool_description := getattr(tool, "description", None):
            input_data["tool_description"] = tool_description  # type: ignore

        if tool_inputs := getattr(tool, "inputs", None):
            input_data["tool_parameters"] = tool_inputs  # type: ignore

        root_span = root_task_span_var.get()
        assert root_span is not None and isinstance(root_span, InMemoryTaskSpan), (
            "Tracing context missing root task span for ToolCallWrapper"
        )
        with root_span.task_span(
            task_name=span_name,
            input=input_data,
        ) as span:
            try:
                response = wrapped(*args, **kwargs)

                output_data = {"response": response}
                if output_type := getattr(tool, "output_type", None):
                    output_data["output_type"] = output_type

                span.record_output(str(output_data))
                return response
            except Exception as e:
                span.log(
                    "Error during tool call execution",
                    {
                        "error_type": e.__class__.__name__,
                        "error_message": str(e),
                        "severity": "error",
                    },
                )
                raise
