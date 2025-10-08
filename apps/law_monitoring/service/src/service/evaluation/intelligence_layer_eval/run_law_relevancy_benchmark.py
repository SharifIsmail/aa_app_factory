import argparse
import os

from law_relevancy_eval_logic import (  # type: ignore
    LawRelevancyAggregationLogic,
    LawRelevancyEvaluationLogic,
)
from law_relevancy_task import LawRelevancyTask  # type: ignore
from loguru import logger
from studio_benchmark_runner import run_studio_benchmark  # type: ignore

from service.dependencies import with_settings


def create_and_execute_law_relevancy_benchmark(
    dataset_id: str, benchmark_name: str
) -> None:
    """Create and execute the law relevancy benchmark."""

    # Check for required environment variables
    if not os.environ.get("SERVICE_AUTHENTICATION_TOKEN"):
        logger.error("SERVICE_AUTHENTICATION_TOKEN environment variable not set")
        logger.info(
            "Please set the SERVICE_AUTHENTICATION_TOKEN environment variable to run Studio benchmarks"
        )
        return

    settings = with_settings()

    # Initialize the task and evaluation components
    task = LawRelevancyTask()
    eval_logic = LawRelevancyEvaluationLogic()
    aggregation_logic = LawRelevancyAggregationLogic()

    # Create and execute benchmark
    try:
        run_id = run_studio_benchmark(
            task=task,
            eval_logic=eval_logic,
            aggregation_logic=aggregation_logic,
            dataset_id=dataset_id,
            benchmark_name=benchmark_name,
            studio_url=str(settings.pharia_studio_url),
        )
        logger.info(
            f"Successfully completed law relevancy benchmark with run ID: {run_id}"
        )
    except Exception as e:
        logger.error(f"Error executing benchmark: {e}")
        raise


def main() -> None:
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Run law relevancy benchmark in Intelligence Layer Studio"
    )
    parser.add_argument(
        "dataset_id", help="The ID of the dataset to use for the benchmark"
    )
    parser.add_argument(
        "--benchmark-name",
        default="Law Relevancy Classification Benchmark",
        help="Name for the benchmark (default: Law Relevancy Classification Benchmark)",
    )

    args = parser.parse_args()

    create_and_execute_law_relevancy_benchmark(args.dataset_id, args.benchmark_name)


if __name__ == "__main__":
    main()
