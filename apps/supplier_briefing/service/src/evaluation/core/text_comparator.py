"""LLM-based comparator for text responses."""

import json
import time
from typing import Dict, Optional

from litellm import completion
from loguru import logger

from evaluation.core.evaluation_prompts import TEXT_COMPARISON_PROMPT
from evaluation.intelligence_layer_eval.supplier_briefing_models import (
    TextComparisonDetails,
    TextComparisonResult,
    TextComparisonStatus,
)
from service.dependencies import with_settings
from service.utils import strip_thinking_tags


class LLMResponseError(Exception):
    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(message)
        self.raw_response = raw_response


class TextComparator:
    """Comparator for free text responses using LLM as judge."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def compare(self, golden: str, current: str) -> TextComparisonResult:
        """Compare two text responses using LLM judge."""

        # Handle empty cases
        if not golden and not current:
            return TextComparisonResult(
                is_match=True,
                details=TextComparisonDetails(
                    status=TextComparisonStatus.COMPARED,
                    explanation="Both texts are empty",
                ),
            )

        if not golden or not current:
            return TextComparisonResult(
                is_match=False,
                details=TextComparisonDetails(
                    status=TextComparisonStatus.COMPARED,
                    explanation="One response is empty while the other is not",
                ),
            )

        # Use LLM judge for comparison
        try:
            llm_result = self._llm_compare_texts_with_retry(golden, current)

            return TextComparisonResult(
                is_match=llm_result.get("is_match", False),
                details=TextComparisonDetails(
                    status=TextComparisonStatus.COMPARED,
                    explanation=llm_result.get("reasoning", ""),
                ),
            )

        except Exception as e:
            logger.error(f"LLM text comparison failed: {e}")
            # Fail fast - don't hide errors with fallbacks
            raise RuntimeError(f"Text comparison failed: {e}")

    def _llm_compare_texts_with_retry(self, golden: str, current: str) -> Dict:
        last_exception = None
        last_raw_response = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._llm_compare_texts(golden, current, attempt)
            except (json.JSONDecodeError, LLMResponseError) as e:
                last_exception = e

                # Extract raw response if available
                if isinstance(e, LLMResponseError):
                    last_raw_response = e.raw_response

                if attempt < self.max_retries:
                    error_msg = f"LLM comparison attempt {attempt + 1} failed: {e}"
                    if last_raw_response:
                        error_msg += f". Raw LLM response: {repr(last_raw_response)}"
                    error_msg += f". Retrying in {self.retry_delay}s..."

                    logger.warning(error_msg)
                    time.sleep(self.retry_delay)
                else:
                    error_msg = f"All {self.max_retries + 1} attempts failed"
                    if last_raw_response:
                        error_msg += (
                            f". Last raw LLM response: {repr(last_raw_response)}"
                        )
                    logger.error(error_msg)

        final_error = f"LLM text comparison failed after {self.max_retries + 1} attempts. Last error: {last_exception}"
        if last_raw_response:
            final_error += f". Last raw LLM response: {repr(last_raw_response)}"

        raise RuntimeError(final_error)

    def _llm_compare_texts(self, golden: str, current: str, attempt: int = 0) -> Dict:
        """Use LLM to compare two text responses."""
        # Prepare prompt with emphasis on JSON format for retries
        prompt = TEXT_COMPARISON_PROMPT.format(golden_text=golden, current_text=current)

        if attempt > 0:
            prompt += (
                "\n\nIMPORTANT: Your response MUST be valid JSON format. "
                "Do not include any markdown code blocks, explanations, or additional text. "
                "Respond only with the JSON object containing 'is_match' and 'reasoning' fields."
            )

        messages = [
            {"role": "user", "content": prompt},
        ]

        # Call LLM using LiteLLMModel directly
        logger.debug(f"Calling LLM model for text comparison (attempt {attempt + 1})")
        settings = with_settings()
        response = completion(
            messages=messages, model=settings.model_evaluation, temperature=0
        )

        result_text = strip_thinking_tags(response.choices[0].message.content)

        # Strip markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]  # Remove ```json
        if result_text.startswith("```"):
            result_text = result_text[3:]  # Remove ```
        if result_text.endswith("```"):
            result_text = result_text[:-3]  # Remove trailing ```

        result_text = result_text.strip()

        # Parse JSON response
        try:
            result = json.loads(result_text)

            if not isinstance(result, dict):
                raise ValueError("Response is not a JSON object")
            if "is_match" not in result:
                raise ValueError("Response missing required field 'is_match'")
            if not isinstance(result["is_match"], bool):
                raise ValueError("Field 'is_match' must be a boolean")

            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw LLM response was: {repr(result_text)}")
            raise LLMResponseError(f"LLM response is not valid JSON: {e}", result_text)
