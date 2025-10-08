#!/usr/bin/env python3
"""
Dataset creator for Supplier Briefing evaluation using Intelligence Layer.

This module handles creation of studio compatible datasets from our JSON evaluation data.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List

import pandas as pd
from intelligence_layer.connectors.studio.studio import StudioClient
from intelligence_layer.evaluation import Example
from intelligence_layer.evaluation.dataset.dataset_repository import DatasetRepository
from intelligence_layer.evaluation.dataset.studio_dataset_repository import (
    StudioDatasetRepository,
)
from loguru import logger

from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)
from evaluation.intelligence_layer_eval.dataset_registry import DatasetRegistry
from evaluation.intelligence_layer_eval.eval_config import GOLDEN_DATASET_PATH
from evaluation.intelligence_layer_eval.supplier_briefing_models import (
    PandasObjectData,
    QuestionDifficulty,
    SupplierBriefingExpectedOutput,
    SupplierBriefingInputDetails,
)
from service.core.utils.pandas_json_utils import (
    deserialize_pandas_object_from_json,
)
from service.dependencies import with_settings


class SupplierBriefingDatasetCreator:
    """Creates Intelligence Layer datasets from JSON evaluation data."""

    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self.dataset_repo = dataset_repo

    def _load_json_dataset(
        self, json_path: Path
    ) -> List[Example[SupplierBriefingInputDetails, SupplierBriefingExpectedOutput]]:
        """Load examples from JSON dataset file."""
        logger.info(f"Loading dataset from {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        examples = []
        evaluation_entries = data.get("evaluation_entries")

        for entry in evaluation_entries:
            # Extract input details
            entry_metadata = entry.get("metadata")
            difficulty_raw = entry.get("question_difficulty")
            config_raw = entry.get("pandas_comparison_config")
            if config_raw is None:
                pandas_config = PandasComparisonConfig(
                    mode=PandasComparisonMode.EXACT_MATCH
                )
            else:
                pandas_config = PandasComparisonConfig(**config_raw)
            input_details = SupplierBriefingInputDetails(
                research_question=entry["research_question"],
                language=entry.get("language", "en"),
                metadata={
                    "question_id": entry_metadata.get("question_id"),
                },
                question_difficulty=QuestionDifficulty(difficulty_raw),
                pandas_comparison_config=pandas_config,
            )

            # Extract expected output from ground truth
            ground_truth = entry.get("ground_truth")
            pandas_objects: list[PandasObjectData] = []

            for pandas_object_json in ground_truth.get("pandas_objects_json", []):
                pandas_obj = deserialize_pandas_object_from_json(pandas_object_json)
                if pandas_obj is None:
                    raise ValueError(
                        f"Failed to deserialize pandas object from: {pandas_object_json}"
                    )

                if isinstance(pandas_obj, pd.Series):
                    pandas_objects.append(
                        PandasObjectData(
                            id=f"data_{len(pandas_objects):08x}",
                            pandas_object_json=pandas_object_json,
                        )
                    )
                elif isinstance(pandas_obj, pd.DataFrame):
                    pandas_objects.append(
                        PandasObjectData(
                            id=f"data_{len(pandas_objects):08x}",
                            pandas_object_json=pandas_object_json,
                        )
                    )
                else:
                    raise ValueError(
                        f"Unexpected pandas object type: {type(pandas_obj)}"
                    )

            expected_output = SupplierBriefingExpectedOutput(
                text=ground_truth.get("text"),
                pandas_objects=pandas_objects,
            )

            # Create example
            example = Example(
                input=input_details,
                expected_output=expected_output,
            )
            examples.append(example)

        logger.info(f"Loaded {len(examples)} examples from JSON dataset")
        return examples

    def create_dataset_from_json(
        self, dataset_name: str, json_path: Path, label: str = "default"
    ) -> str:
        """Create IL dataset from JSON file."""
        logger.info(f"Creating dataset '{dataset_name}' from {json_path}")

        # Load examples
        examples = self._load_json_dataset(json_path)

        if not examples:
            raise ValueError(f"No examples found in {json_path}")

        # Create dataset (Studio repository)
        dataset = self.dataset_repo.create_dataset(
            examples=examples,
            dataset_name=f"{dataset_name}_{label}",
            metadata={
                "source_file": str(json_path),
                "example_count": len(examples),
                "label": label,
            },
        )

        logger.info(f"Created dataset with ID: {dataset.id}")
        return dataset.id


def create_studio_dataset(
    dataset_name: str,
    json_path: Path,
    project_name: str,
    label: str = "default",
) -> str:
    """Create dataset in Intelligence Layer Studio."""
    settings = with_settings()
    # Create Studio client
    client = StudioClient(
        project=project_name,
        create_project=True,
        auth_token=settings.authentication_token.get_secret_value(),
        studio_url=str(settings.studio_url),
    )

    # Create studio repository
    studio_repo = StudioDatasetRepository(client)

    # Create dataset
    creator = SupplierBriefingDatasetCreator(studio_repo)
    dataset_id = creator.create_dataset_from_json(dataset_name, json_path, label)

    logger.info(f"Created Studio dataset in project '{project_name}'")
    return dataset_id


def main() -> None:
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Create Intelligence Layer datasets from JSON evaluation data"
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        type=Path,
        default=GOLDEN_DATASET_PATH,
        help="Path to JSON dataset file (default: golden dataset)",
    )
    parser.add_argument(
        "--name",
        default="supplier_briefing_golden",
        help="Name for the dataset",
    )
    parser.add_argument(
        "--label",
        default="golden",
        help="Label for the dataset (e.g., 'golden', 'current')",
    )
    parser.add_argument(
        "--project-name",
        default="supplier-briefing-evaluation",
        help="Studio project name (default: supplier-briefing-evaluation)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    settings = with_settings()
    token = settings.authentication_token

    # Create Studio dataset
    studio_id = create_studio_dataset(
        dataset_name=args.name,
        json_path=args.json_path,
        label=args.label,
        project_name=args.project_name,
    )
    print(f"✅ Created Studio dataset with ID: {studio_id}")

    # Register Studio dataset ID in the registry
    registry = DatasetRegistry()
    registry.register_dataset(args.label, studio_id)
    print(f"✅ Registered dataset ID for label '{args.label}'")


if __name__ == "__main__":
    main()
