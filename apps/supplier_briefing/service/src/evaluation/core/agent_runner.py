import uuid
from typing import List, Tuple

from loguru import logger

from evaluation.intelligence_layer_eval.supplier_briefing_models import (
    PandasObjectData,
    SupplierBriefingOutput,
)
from service.agent_core.constants import (
    REPO_AGENT_RESPONSE,
    REPO_PANDAS_OBJECTS,
)
from service.agent_core.data_query_orchestration.data_query_service import (
    DataQueryService,
)
from service.agent_core.models import WorkLog
from service.dependencies import with_settings
from service.work_log_manager import WorkLogManager


def run_research_system(
    research_question: str,
) -> Tuple[str, WorkLog]:
    """
    Run the production research system and return results.

    Args:
        research_question: The question to research

    Returns:
        Tuple of (research_result, work_log)
    """
    logger.info(f"Running research system for question: {research_question}")

    # Generate unique ID for this run
    execution_id = f"eval_{uuid.uuid4().hex[:8]}"

    # Run the research system
    try:
        work_log_manager = WorkLogManager()

        work_log = DataQueryService(with_settings(), work_log_manager).run(
            research_question,
            execution_id,
            enable_explainability=False,
        )
        final_result = work_log.data_storage.retrieve_all_from_repo(
            REPO_AGENT_RESPONSE
        )["agent_response"]["data"]

        return final_result, work_log

    except Exception:
        logger.error(f"Failed to run research system for question: {research_question}")
        raise


def parse_system_output(
    research_result: str, work_log: WorkLog
) -> SupplierBriefingOutput:
    """
    Parse system output into SupplierBriefingOutput format.

    Args:
        research_result: The text result from the research system
        work_log: The work log from the research execution

    Returns:
        SupplierBriefingOutput object with text and pandas objects
    """
    logger.debug("Parsing system output")

    # Extract text result from multiple sources
    text_parts = []

    # 1. Use research_result if available
    if research_result:
        text_parts.append(research_result)

    # 2. Extract from agent_response repository as fallback
    try:
        if work_log.data_storage:
            agent_responses = work_log.data_storage.retrieve_all_from_repo(
                REPO_AGENT_RESPONSE
            )
            for key, value in agent_responses.items():
                if isinstance(value, dict) and "data" in value:
                    text_parts.append(value["data"])
                elif isinstance(value, str):
                    text_parts.append(value)
    except Exception as e:
        logger.debug(f"Could not extract from agent_response: {e}")

    # Combine all text parts, removing duplicates while preserving order
    seen = set()
    unique_parts = []
    for part in text_parts:
        if part and part not in seen:
            seen.add(part)
            unique_parts.append(part)

    text = "\n\n".join(unique_parts) if unique_parts else ""

    # Extract pandas_objects using the updated function
    pandas_objects = _extract_pandas_objects_from_work_log(work_log)

    return SupplierBriefingOutput(
        text=text,
        pandas_objects=pandas_objects,
    )


def _extract_pandas_objects_from_work_log(work_log: WorkLog) -> List[PandasObjectData]:
    """
    Extract pandas objects from work log.

    Args:
        work_log: The work log from research execution

    Returns:
        List of PandasObjectData objects with metadata
    """
    pandas_objects: List[PandasObjectData] = []

    # Ensure work_log has data_storage
    if not hasattr(work_log, "data_storage") or not work_log.data_storage:
        raise ValueError("WorkLog missing data_storage attribute")

    # Extract pandas objects (as json strings)
    pandas_objects_jsons = work_log.data_storage.retrieve_all_from_repo(
        REPO_PANDAS_OBJECTS
    )

    for i, (data_id, pandas_object_json) in enumerate(pandas_objects_jsons.items(), 1):
        if pandas_object_json is None:
            logger.error("None pandas data for ID: {}", data_id)
            raise ValueError(f"None pandas data for ID: {data_id}")

        pandas_object = PandasObjectData(
            id=data_id,
            pandas_object_json=pandas_object_json,
        )
        pandas_objects.append(pandas_object)

    return pandas_objects
