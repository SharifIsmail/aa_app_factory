from typing import Any, Callable

import smolagents
from intelligence_layer.connectors import StudioClient
from smolagents import CodeAgent, MultiStepAgent, Tool, ToolCallingAgent, models
from wrapt import wrap_function_wrapper  # type: ignore[import-untyped]

from service.tracing.smolagents_wrappers import (
    ModelWrapper,
    RunWrapper,
    StepStreamWrapper,
    ToolCallWrapper,
)


class SmolagentsStudioInstrumentor:
    def __init__(
        self, studio_url: str, auth_token: str, studio_project_name: str
    ) -> None:
        self._studio_url = studio_url
        self._auth_token = auth_token
        self._studio_project_name = studio_project_name

        self._original_run_method: Callable[..., Any] | None = None
        self._original_step_stream_methods: dict[type, Callable[..., Any]] | None = None
        self._original_tool_call_method: Callable[..., Any] | None = None
        self._original_model_generate_methods: dict[type, Callable[..., Any]] | None = (
            None
        )

    def instrument(self) -> None:
        studio_client = StudioClient(
            project=self._studio_project_name,
            studio_url=self._studio_url,
            auth_token=self._auth_token,
            create_project=True,
        )

        run_wrapper = RunWrapper(studio_client=studio_client)
        self._original_run_method = getattr(MultiStepAgent, "run", None)  # type: ignore
        wrap_function_wrapper(
            module="smolagents",
            name="MultiStepAgent.run",
            wrapper=run_wrapper,
        )

        self._original_step_stream_methods = {}
        step_stream_wrapper = StepStreamWrapper()
        for step_cls in [CodeAgent, ToolCallingAgent]:
            self._original_step_stream_methods[step_cls] = getattr(  # type: ignore
                step_cls, "_step_stream", None
            )
            if self._original_step_stream_methods != None:
                wrap_function_wrapper(
                    module="smolagents",
                    name=f"{step_cls.__name__}._step_stream",
                    wrapper=step_stream_wrapper,
                )

        self._original_model_generate_methods = {}

        exported_model_subclasses = [
            attr
            for _, attr in vars(smolagents).items()
            if isinstance(attr, type) and issubclass(attr, models.Model)
        ]

        for model_subclass in exported_model_subclasses:
            model_subclass_wrapper = ModelWrapper()

            self._original_model_generate_methods[model_subclass] = getattr(
                model_subclass, "generate"
            )
            wrap_function_wrapper(
                module="smolagents",
                name=model_subclass.__name__ + ".generate",
                wrapper=model_subclass_wrapper,
            )

        tool_call_wrapper = ToolCallWrapper()
        self._original_tool_call_method = getattr(Tool, "__call__", None)  # type: ignore
        wrap_function_wrapper(
            module="smolagents",
            name="Tool.__call__",
            wrapper=tool_call_wrapper,
        )

    def uninstrument(self) -> None:
        if self._original_run_method is not None:
            MultiStepAgent.run = self._original_run_method  # type: ignore
            self._original_run_method = None

        if self._original_step_stream_methods is not None:
            for (
                step_cls,
                original_step_method,
            ) in self._original_step_stream_methods.items():
                setattr(step_cls, "step", original_step_method)
            self._original_step_stream_methods = None

        if self._original_model_generate_methods is not None:
            for (
                model_subclass,
                original_model_generate_method,
            ) in self._original_model_generate_methods.items():
                setattr(model_subclass, "generate", original_model_generate_method)
            self._original_model_generate_methods = None

        if self._original_tool_call_method is not None:
            Tool.__call__ = self._original_tool_call_method  # type: ignore
            self._original_tool_call_method = None
