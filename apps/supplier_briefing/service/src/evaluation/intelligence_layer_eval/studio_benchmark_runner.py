from typing import Optional

from intelligence_layer.connectors.studio.studio import StudioClient
from intelligence_layer.core import Task
from intelligence_layer.evaluation import EvaluationLogic
from intelligence_layer.evaluation.aggregation.aggregator import AggregationLogic
from intelligence_layer.evaluation.benchmark.studio_benchmark import (
    StudioBenchmarkRepository,
)
from loguru import logger

from service.dependencies import with_settings


def run_studio_benchmark(
    task: Task,
    eval_logic: EvaluationLogic,
    aggregation_logic: AggregationLogic,
    dataset_id: str,
    benchmark_name: str,
    studio_token: Optional[str] = None,
    project_name: str = "supplier-briefing-evaluation",
) -> str:
    """
    Run a benchmark in Studio and return the run ID.

    Args:
        task: The task to evaluate
        eval_logic: Evaluation logic for individual examples
        aggregation_logic: Aggregation logic for results
        dataset_id: ID of the dataset to use
        benchmark_name: Name for the benchmark
        studio_token: Studio API token (uses env var if not provided)
        project_name: Studio project name

    Returns:
        The benchmark run ID

    Raises:
        ValueError: If studio token is not available
        RuntimeError: If benchmark creation or execution fails
    """

    # Create Studio client
    settings = with_settings()
    client = StudioClient(
        project=project_name,
        create_project=True,
        auth_token=settings.authentication_token.get_secret_value(),
        studio_url=str(settings.studio_url),
    )

    # Create benchmark repository
    benchmark_repo = StudioBenchmarkRepository(client)

    # Create benchmark
    logger.info(f"Creating benchmark '{benchmark_name}' with dataset {dataset_id}")
    benchmark = benchmark_repo.create_benchmark(
        dataset_id=dataset_id,
        eval_logic=eval_logic,
        aggregation_logic=aggregation_logic,
        name=benchmark_name,
        description=f"Benchmark for {type(task).__name__} evaluation",
    )

    if not benchmark:
        raise RuntimeError(f"Failed to create benchmark '{benchmark_name}'")

    logger.info(f"Created benchmark {benchmark.name} with ID {benchmark.id}")

    # Execute benchmark
    logger.info(f"Executing benchmark {benchmark.name}...")
    run_id = benchmark.execute(
        task=task,
        name=f"{type(task).__name__} benchmark run",
        description=f"Evaluation run for {type(task).__name__}",
        labels=None,
        metadata={
            "task": type(task).__name__,
            "evaluation_logic": type(eval_logic).__name__,
            "aggregation_logic": type(aggregation_logic).__name__,
        },
    )

    logger.info(f"Benchmark execution completed. Run ID: {run_id}")
    return run_id
