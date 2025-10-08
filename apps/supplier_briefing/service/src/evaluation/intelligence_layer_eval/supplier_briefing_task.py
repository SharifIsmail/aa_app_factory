"""
Supplier Briefing Task for Intelligence Layer evaluation.

This module provides the Task wrapper that integrates our research agent
into the Intelligence Layer evaluation framework.
"""

import logging
import uuid

from intelligence_layer.core import Task, TaskSpan
from loguru import logger

from evaluation.core.agent_runner import parse_system_output, run_research_system
from evaluation.intelligence_layer_eval.supplier_briefing_models import (
    SupplierBriefingInputDetails,
    SupplierBriefingOutput,
)


class SupplierBriefingTask(Task[SupplierBriefingInputDetails, SupplierBriefingOutput]):
    """Task to execute supplier briefing research and return structured results."""

    def do_run(
        self, input: SupplierBriefingInputDetails, task_span: TaskSpan
    ) -> SupplierBriefingOutput:
        """Execute the research agent and return structured output."""

        # Generate a unique ID for this evaluation
        eval_id = f"eval_{uuid.uuid4().hex[:8]}"

        # Add question_id from metadata if available
        if "question_id" in input.metadata:
            eval_id = input.metadata["question_id"]

        try:
            # Execute research using existing agent_runner functions
            research_result, work_log = run_research_system(
                research_question=input.research_question
            )

            supplier_briefing_output = parse_system_output(research_result, work_log)

            logger.info(f"Extracted text: {len(supplier_briefing_output.text)} chars")
            logger.info(
                f"Extracted pandas objects: {len(supplier_briefing_output.pandas_objects)}"
            )

            logger.info(f"Successfully completed research for {eval_id}")
            return supplier_briefing_output

        except Exception as e:
            logger.error(f"Research failed for {eval_id}: {e}")
            logger.error(f"Error type: {type(e).__name__}")

            # Return structured error response (don't raise exception)
            # IL framework expects Task to always return valid output type
            raise


# Example usage and testing
if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create task instance
    task = SupplierBriefingTask()

    # Test with sample input
    test_input = SupplierBriefingInputDetails(
        research_question='What risk information do we have about the business partner "InfoFinance Technologies GmbH" with the ID "1514"?',
        language="en",
        metadata={"question_id": "test_risk_matrix_business_partner"},
    )

    logger.info("=" * 60)
    logger.info("TESTING SUPPLIER BRIEFING TASK")
    logger.info("=" * 60)

    # Execute task with mock TaskSpan for testing
    class MockTaskSpan:
        pass

    try:
        result = task.do_run(test_input, MockTaskSpan())  # type: ignore

        logger.info("=" * 60)
        logger.info("TASK EXECUTION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Text output length: {len(result.text)}")
        logger.info(f"Number of pandas objects: {len(result.pandas_objects)}")

        if result.pandas_objects:
            for i, pandas_object in enumerate(result.pandas_objects):
                logger.info(f"Pandas object {i + 1}: {pandas_object.id}")

        logger.info("=" * 60)
        logger.info("✅ Task execution successful!")

    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ Task execution failed!")
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        raise
