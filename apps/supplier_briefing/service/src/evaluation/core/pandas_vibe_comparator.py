from __future__ import annotations

import json
import time
from typing import Any

from litellm import completion
from loguru import logger

from evaluation.core.evaluation_prompts import DATAFRAME_VIBE_PROMPT
from evaluation.intelligence_layer_eval.supplier_briefing_models import (
    VibeCheckResult,
    VibeCheckStatus,
)
from service.dependencies import with_settings
from service.utils import strip_thinking_tags


class LLMVibeResponseError(Exception):
    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message)
        self.raw_response = raw_response


class PandasVibeComparator:
    """LLM-based continuous similarity scorer for lists of dataframe-like dicts.

    Expects inputs to be pre-cleaned lists of dicts with keys: "type" and "data".
    Returns a score in [0, 1] with brief reasoning via ComparisonResult.details.
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def compare(
        self,
        golden: list[dict[str, str]],
        current: list[dict[str, str]],
        research_question: str | None = None,
    ) -> VibeCheckResult:
        """Compare two lists of cleaned dict representations of pandas dataframes."""
        # Both empty -> perfect match vibe
        if not golden and not current:
            return VibeCheckResult(
                status=VibeCheckStatus.EXACT_MATCH_SKIP,
                score=1.0,
                reasoning="Both sides empty",
            )

        # If one side empty -> no overlap
        if (not golden and current) or (golden and not current):
            return VibeCheckResult(
                status=VibeCheckStatus.NO_OVERLAP_EMPTY_SKIP,
                score=0.0,
                reasoning="One side is empty",
            )

        # LLM judge
        try:
            score, reasoning = self._llm_score_with_retry(
                golden, current, research_question
            )
            # Clamp to [0, 1]
            score = max(0.0, min(1.0, float(score)))
            return VibeCheckResult(
                status=VibeCheckStatus.LLM_JUDGED,
                score=score,
                reasoning=reasoning,
            )
        except Exception as e:
            logger.error(f"LLM dataframe vibe comparison failed: {e}")
            raise RuntimeError(f"Dataframe vibe comparison failed: {e}")

    def _summarize_objects(
        self, objects: list[dict[str, str]], max_rows: int = 20
    ) -> list[dict[str, str]]:
        summarized: list[dict[str, Any]] = []
        for obj in objects:
            obj_type = obj.get("type")
            data = obj.get("data")
            summary_entry: dict[str, Any] = {"type": obj_type}
            try:
                # Try common pandas JSON layouts
                if isinstance(data, dict):
                    # If there is an explicit 'data' key containing rows
                    if "data" in data and isinstance(data["data"], list):
                        rows = data["data"][:max_rows]
                        schema = list(
                            data.get("columns", [])
                        ) or self._infer_columns_from_rows(rows)
                        summary_entry["schema"] = schema
                        summary_entry["sample_rows"] = rows
                    # records/rows layout
                    elif "records" in data and isinstance(data["records"], list):
                        rows = data["records"][:max_rows]
                        summary_entry["schema"] = self._infer_columns_from_rows(rows)
                        summary_entry["sample_rows"] = rows
                    elif "rows" in data and isinstance(data["rows"], list):
                        rows = data["rows"][:max_rows]
                        summary_entry["schema"] = self._infer_columns_from_rows(rows)
                        summary_entry["sample_rows"] = rows
                    else:
                        # Column-wise dict of lists
                        keys = list(data.keys())
                        summary_entry["schema"] = keys
                        sampled_columns: dict[str, Any] = {}
                        for k in keys:
                            v = data.get(k)
                            if isinstance(v, list):
                                sampled_columns[k] = v[:max_rows]
                            else:
                                sampled_columns[k] = v
                        summary_entry["sample_columns"] = sampled_columns
                elif isinstance(data, list):
                    # List of row dicts or values
                    summary_entry["schema"] = self._infer_columns_from_rows(data)
                    summary_entry["sample_rows"] = data[:max_rows]
                else:
                    # Fallback to string repr truncated
                    summary_entry["summary"] = str(data)[:500]
            except Exception as e:
                summary_entry["summary_error"] = f"Failed to summarize: {e}"
            summarized.append(summary_entry)
        return summarized

    def _infer_columns_from_rows(self, rows: list[Any]) -> list[str]:
        for row in rows:
            if isinstance(row, dict):
                return list(row.keys())
            if isinstance(row, list):
                return [f"col_{i}" for i in range(len(row))]
        return []

    def _llm_score_with_retry(
        self,
        golden: list[dict[str, Any]],
        current: list[dict[str, Any]],
        research_question: str | None,
    ) -> tuple[float, str]:
        last_exception: Exception | None = None
        last_raw_response: str | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._llm_score(golden, current, research_question, attempt)
            except Exception as e:
                last_exception = e
                if isinstance(e, LLMVibeResponseError):
                    last_raw_response = e.raw_response

                if attempt < self.max_retries:
                    msg = f"LLM vibe attempt {attempt + 1} failed: {e}"
                    if last_raw_response:
                        msg += f". Raw: {repr(last_raw_response)}"
                    msg += f". Retrying in {self.retry_delay}s..."
                    logger.warning(msg)
                    time.sleep(self.retry_delay)
                else:
                    msg = f"All {self.max_retries + 1} LLM vibe attempts failed"
                    if last_raw_response:
                        msg += f". Last raw: {repr(last_raw_response)}"
                    logger.error(msg)

        final_error = f"LLM vibe comparison failed after {self.max_retries + 1} attempts. Last error: {last_exception}"
        if last_raw_response:
            final_error += f". Last raw: {repr(last_raw_response)}"
        raise RuntimeError(final_error)

    def _llm_score(
        self,
        golden: list[dict[str, Any]],
        current: list[dict[str, Any]],
        research_question: str | None,
        attempt: int = 0,
    ) -> tuple[float, str]:
        # For retry attempts, reduce payload size by summarizing
        if attempt == 0:
            golden_payload = golden
            current_payload = current
        else:
            golden_payload = self._summarize_objects(golden, max_rows=20)
            current_payload = self._summarize_objects(current, max_rows=20)

        # Prepare prompt; use compact JSON to reduce tokens
        golden_json = json.dumps(golden_payload, ensure_ascii=False)
        current_json = json.dumps(current_payload, ensure_ascii=False)

        prompt = DATAFRAME_VIBE_PROMPT.format(
            research_question=(research_question or ""),
            golden_json=golden_json,
            current_json=current_json,
        )
        if attempt > 0:
            prompt += (
                "\n\nIMPORTANT: Your response MUST be valid JSON format. "
                "Do not include any markdown code blocks, explanations, or additional text. "
                "Respond only with the JSON object containing 'score' and 'reasoning'."
            )

        messages = [{"role": "user", "content": prompt}]

        logger.debug(
            f"Calling LLM model for dataframe vibe comparison (attempt {attempt + 1})"
        )

        settings = with_settings()
        response = completion(messages=messages, model=settings.model_evaluation)
        result_text = strip_thinking_tags(response.choices[0].message.content)

        # Strip possible code fences
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()

        try:
            result = json.loads(result_text)
            if not isinstance(result, dict):
                raise ValueError("Response is not a JSON object")
            if "score" not in result:
                raise ValueError("Response missing required field 'score'")
            score_val = float(result["score"])  # may raise ValueError
            reasoning = str(result.get("reasoning", ""))
            return score_val, reasoning
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM vibe response as JSON: {e}")
            logger.error(f"Raw LLM vibe response was: {repr(result_text)}")
            raise LLMVibeResponseError(
                f"LLM vibe response is not valid JSON: {e}", result_text
            )
