#!/usr/bin/env python3
"""
Run Supplier Briefing benchmark using Intelligence Layer Studio.

This script properly uses the Studio SDK framework for evaluation.
"""

import argparse
import logging
import sys
from datetime import datetime

from loguru import logger

from evaluation.intelligence_layer_eval.dataset_registry import DatasetRegistry
from evaluation.intelligence_layer_eval.studio_benchmark_runner import (
    run_studio_benchmark,
)
from evaluation.intelligence_layer_eval.supplier_briefing_eval_logic import (
    SupplierBriefingAggregationLogic,
    SupplierBriefingEvaluationLogic,
)
from evaluation.intelligence_layer_eval.supplier_briefing_task import (
    SupplierBriefingTask,
)
from service.tracing.init import initialize_tracing


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run Supplier Briefing benchmark in Pharia Studio"
    )
    parser.add_argument(
        "dataset_id",
        nargs="?",
        help="The dataset ID to use. If omitted, will use the 'golden' dataset from the registry.",
    )
    parser.add_argument(
        "--benchmark-name",
        default=None,
        help="Name for the benchmark. If omitted, a unique name will be generated ",
    )
    parser.add_argument(
        "--project-name",
        default="supplier-briefing-evaluation",
        help="Studio project name (default: supplier-briefing-evaluation)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Resolve dataset_id default from registry if not provided
    dataset_id = args.dataset_id
    if dataset_id is None:
        registry = DatasetRegistry()
        dataset_id = registry.get_studio_id("golden")
        if not dataset_id:
            logger.error("No dataset ID found in registry for label 'golden'")
            logger.info("Create and register it with: uv run create_dataset")
            sys.exit(1)

    # Compute default benchmark name with timestamp when not provided
    benchmark_name = (
        args.benchmark_name
        if args.benchmark_name is not None
        else f"Supplier Briefing Evaluation - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    initialize_tracing()

    # Initialize components
    logger.info("Initializing evaluation components...")
    task = SupplierBriefingTask()
    eval_logic = SupplierBriefingEvaluationLogic()
    aggregation_logic = SupplierBriefingAggregationLogic()

    # Run benchmark
    logger.info(f"Starting benchmark '{benchmark_name}'...")
    run_id = run_studio_benchmark(
        task=task,
        eval_logic=eval_logic,
        aggregation_logic=aggregation_logic,
        dataset_id=dataset_id,
        benchmark_name=benchmark_name,
        project_name=args.project_name,
    )

    logger.info("=" * 60)
    logger.info("BENCHMARK COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Dataset ID: {dataset_id}")
    logger.info(f"Benchmark Name: {benchmark_name}")
    logger.info(f"Project: {args.project_name}")
    logger.info("=" * 60)

    print(f"✅ Successfully completed benchmark with run ID: {run_id}")


if __name__ == "__main__":
    main()
