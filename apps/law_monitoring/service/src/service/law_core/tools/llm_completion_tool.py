import hashlib
import os
import time

from loguru import logger
from smolagents.models import LiteLLMModel
from smolagents.tools import Tool

from service.law_core.models import ToolLog, WorkLog
from service.law_core.persistence.cache_service import cache_service
from service.metrics import llm_call_duration_seconds


class LLMCompletionTool(Tool):
    name = "llm_completion"
    description = "Performs an LLM completion based on a prompt."
    inputs = {
        "prompt": {
            "type": "string",
            "description": "The prompt to use for the completion.",
        },
        "purpose": {
            "type": "string",
            "description": "The business purpose of this LLM call (e.g., 'Extracting topics from law text').",
        },
    }
    output_type = "string"

    def __init__(
        self, lite_llm_model: LiteLLMModel, execution_id: str, work_log: WorkLog
    ):
        self.model = lite_llm_model
        self.execution_id = execution_id
        self.work_log = work_log
        self.is_initialized = True

    def _generate_cache_id(self, prompt: str, purpose: str) -> str:
        """Generate a unique cache ID based on the prompt, purpose, and model ID."""
        cache_key = f"llm_completion_{purpose}_{prompt}_{self.model.model_id}"
        return hashlib.sha256(cache_key.encode()).hexdigest()

    def forward(self, prompt: str, purpose: str) -> str:
        start_time = time.time()

        # Create tool log with purpose instead of tool name, and without the prompt for security
        tool_log = ToolLog(tool_name=purpose, params={})
        self.work_log.tool_logs.append(tool_log)

        # Generate cache ID
        cache_id = self._generate_cache_id(prompt, purpose)

        try:
            # Check if result is in cache
            cached_result = cache_service.load_from_cache(cache_id)
            if cached_result:
                logger.info(f"Using cached LLM result for purpose: {purpose}")
                tool_log.result = cached_result
                time.sleep(int(os.getenv("WAIT_ON_CACHED_RESULT", "2")))
                return cached_result

            # Let exceptions propagate all the way up
            logger.info(
                f"Making LLM call to {self.model.model_id} for purpose: {purpose}"
            )
            messages = [{"role": "user", "content": prompt}]
            response = self.model(messages)

            if response is None or response.raw is None:
                logger.error("LLM call failed: received None response")
                raise Exception("LLM call failed: received None response")

            if not hasattr(response.raw, "choices") or not response.raw.choices:
                logger.error("LLM call failed: no choices in response")
                raise Exception("LLM call failed: no choices in response")

            result = response.raw.choices[0].message.content

            # Cache the result
            cache_service.save_to_cache(cache_id, result)
            logger.info("LLM call completed and cached successfully")

            tool_log.result = result
            return result

        finally:
            # Record timing metrics
            duration = time.time() - start_time
            llm_call_duration_seconds.labels(purpose=purpose).observe(duration)
