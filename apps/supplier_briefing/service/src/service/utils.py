import dataclasses
import re
from datetime import datetime
from typing import Any, List, Optional

import pandas

from service.core.utils.pandas_json_utils import serialize_pandas_object_to_json
from service.dependencies import with_settings


def strip_thinking_tags(content: str, thinking_tag_end: str | None = None) -> str:
    """Remove everything before and including the first thinking tag.

    Args:
        content: The text content to process
        thinking_tag_end: The end tag to search for. If None, loads from settings (default: None)

    Returns:
        The content with thinking tags stripped
    """
    if not content:
        return content

    if thinking_tag_end is None:
        settings = with_settings()
        thinking_tag_end = settings.thinking_tag_end

    # Find the first occurrence of the thinking tag (case-insensitive)
    lower_content = content.lower()
    tag_pos = lower_content.find(thinking_tag_end.lower())

    if tag_pos != -1:
        # Remove everything up to and including the thinking tag
        cleaned_content = content[tag_pos + len(thinking_tag_end) :]
    else:
        # No thinking tag found, return original content
        cleaned_content = content

    # Clean up extra whitespace left behind
    cleaned_content = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned_content)
    cleaned_content = cleaned_content.strip()

    return cleaned_content


def make_json_serializable(obj: Any) -> Any:
    """Recursively convert complex Python objects to JSON-serializable formats.

    Handles pandas DataFrames/Series, datetime objects, dataclasses, and custom objects
    by converting them to basic Python types (dict, list, str, int, float, bool, None).
    """
    # Handle pandas objects using specialized serialization
    if isinstance(obj, (pandas.DataFrame, pandas.Series)):
        return serialize_pandas_object_to_json(obj)

    # Handle datetime objects
    elif isinstance(obj, datetime):
        return obj.isoformat()

    # Handle dataclasses
    elif dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return make_json_serializable(dataclasses.asdict(obj))

    # Handle collections
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_json_serializable(item) for item in obj)

    # Handle custom objects with __dict__
    elif hasattr(obj, "__dict__") and not isinstance(
        obj, (str, int, float, bool, type(None))
    ):
        try:
            return {k: make_json_serializable(v) for k, v in obj.__dict__.items()}
        except (AttributeError, TypeError):
            # Fallback to string representation for objects that can't be serialized
            return str(obj)

    # Return primitive types as-is
    return obj


def filter_agent_conversation_bloat(agent_steps: Optional[List[Any]]) -> List[Any]:
    """
    Remove bloat and dynamic data from agent conversation for consistent caching.

    This function filters out massive system prompts, repetitive task definitions,
    and all dynamic data (timestamps, IDs, UUIDs) that change between runs and
    prevent LLM response caching.

    REMOVES:
    - MessageRole.SYSTEM messages (tool documentation bloat - 36K+ chars each)
    - MessageRole.USER messages (repetitive task definition bloat)
    - TaskStep objects entirely (contain massive task definitions)
    - All timestamps (start_time, end_time, created)
    - All UUIDs and dynamic IDs (model response IDs, tool call IDs)
    - Duration fields

    PRESERVES:
    - Core conversation structure
    - All ASSISTANT responses and reasoning
    - All TOOL_CALL and TOOL_RESPONSE messages (database results, analysis)
    - All observations and step data
    - Model outputs and tool arguments

    Args:
        agent_steps: List of agent step objects from smolagents framework

    Returns:
        List of filtered agent steps with same structure, reduced bloat, no dynamic data
    """
    if not agent_steps:
        return []

    import re

    filtered_steps = []

    for step in agent_steps:
        # Handle TaskStep objects - SKIP entirely to avoid massive task definitions
        if (
            hasattr(step, "task")
            and hasattr(step, "__class__")
            and "TaskStep" in str(step.__class__)
        ):
            # Skip TaskStep entirely - contains massive task definition
            continue

        # Handle ActionStep objects with model_input_messages
        if hasattr(step, "model_input_messages") and step.model_input_messages:
            # Filter messages
            filtered_messages = []
            for msg in step.model_input_messages:
                # Check the role
                if isinstance(msg, dict) and "role" in msg:
                    role = msg["role"]
                    # Skip SYSTEM messages (tool documentation bloat)
                    if str(role) == "MessageRole.SYSTEM":
                        continue
                    # Skip USER messages (repetitive task definition bloat)
                    if str(role) == "MessageRole.USER":
                        continue

                # KEEP EVERYTHING ELSE - ASSISTANT, TOOL_CALL, TOOL_RESPONSE, etc.
                filtered_messages.append(msg)

            # Keep the step but with filtered messages
            step.model_input_messages = filtered_messages

        # Convert step to string for normalization only at the end
        step_str = str(step)

        # Simple, safe replacements - don't break the structure
        step_str = step_str.replace("start_time=", "start_time=0#")
        step_str = step_str.replace("end_time=", "end_time=0#")
        step_str = step_str.replace("duration=", "duration=0#")
        step_str = step_str.replace("created=", "created=0#")
        step_str = step_str.replace("call_", "normalized_")

        # Replace chatcmpl- and UUID patterns more aggressively
        step_str = re.sub(r"chatcmpl-[a-f0-9\-]+", "normalized_id", step_str)
        step_str = re.sub(r"normalized_[a-f0-9\-]+", "normalized_id", step_str)

        # Clean up the markers
        step_str = re.sub(
            r"(start_time|end_time|duration)=0#[\d\.]+", r"\1=0", step_str
        )
        step_str = re.sub(r"created=0#\d+", "created=0", step_str)

        filtered_steps.append(step_str)

    return filtered_steps


def standardize_date_format(date_string: str) -> str:
    """
    Convert mixed date formats to mm/yyyy-mm/yyyy format.

    Handles:
    - 'dd.mm.yyyy - dd.mm.yyyy' -> 'mm/yyyy-mm/yyyy'
    - 'mm/yyyy-mm/yyyy' -> 'mm/yyyy-mm/yyyy' (already correct)
    """
    if pandas.isna(date_string):
        return date_string

    # Check if it's already in mm/yyyy-mm/yyyy format
    if re.match(r"^\d{2}/\d{4}-\d{2}/\d{4}$", str(date_string)):
        return date_string

    # Handle dd.mm.yyyy - dd.mm.yyyy format
    if re.match(r"^\d{2}\.\d{2}\.\d{4} - \d{2}\.\d{2}\.\d{4}$", str(date_string)):
        # Split the date range
        start_date, end_date = date_string.split(" - ")

        # Parse start date
        start_dt = datetime.strptime(start_date, "%d.%m.%Y")
        start_formatted = start_dt.strftime("%m/%Y")

        # Parse end date
        end_dt = datetime.strptime(end_date, "%d.%m.%Y")
        end_formatted = end_dt.strftime("%m/%Y")

        return f"{start_formatted}-{end_formatted}"

    # If format is not recognized, return as-is
    return date_string
