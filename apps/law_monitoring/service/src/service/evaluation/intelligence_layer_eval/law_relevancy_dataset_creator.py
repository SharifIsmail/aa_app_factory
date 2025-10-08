import json
from pathlib import Path
from typing import List

from law_relevancy_task import LawRelevancyInputDetails  # type: ignore
from loguru import logger
from pharia_studio_sdk.connectors import StudioClient
from pharia_studio_sdk.evaluation import Example
from pharia_studio_sdk.evaluation.dataset.dataset_repository import DatasetRepository
from pharia_studio_sdk.evaluation.dataset.file_dataset_repository import (
    FileDatasetRepository,
)
from pharia_studio_sdk.evaluation.dataset.studio_dataset_repository import (
    StudioDatasetRepository,
)

from service.dependencies import with_settings


class LawRelevancyDatasetCreator:
    """Creation of dataset for evaluation of LawRelevancyTask."""

    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self.dataset_repo = dataset_repo

    def _load_labeled_samples(
        self, dataset_dir: str
    ) -> List[Example[LawRelevancyInputDetails, bool]]:
        """Load labeled samples from the evaluation dataset directory."""
        examples: List[Example[LawRelevancyInputDetails, bool]] = []
        dataset_path = Path(dataset_dir)

        if not dataset_path.exists():
            logger.warning(f"Dataset directory {dataset_dir} does not exist")
            return examples

        # Load all JSON files in the directory
        json_files = list(dataset_path.glob("*.json"))

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    sample_data = json.load(f)

                # Skip summary files
                if json_file.name in [
                    "labeling_summary.json",
                    "collection_summary.json",
                ]:
                    continue

                # Extract data from the sample
                law_text = sample_data.get("law_text", "")
                metadata = sample_data.get("metadata", {})
                ground_truth = sample_data.get("ground_truth", {})

                # Get title from metadata or use filename
                law_title = metadata.get("title", json_file.stem)

                # Determine expected output from ground truth
                expected_output = ground_truth.get("is_relevant", False)

                # Create input details
                input_details = LawRelevancyInputDetails(
                    law_text=law_text,
                    law_title=law_title,
                    metadata=metadata,
                )

                # Create example
                example = Example(input=input_details, expected_output=expected_output)

                examples.append(example)
                logger.debug(f"Loaded example from {json_file.name}")

            except Exception as e:
                logger.error(f"Error loading sample from {json_file}: {e}")
                continue

        logger.info(f"Successfully loaded {len(examples)} examples from {dataset_dir}")
        return examples

    def create_dataset(self, dataset_name: str, labeled_dataset_dir: str) -> str:
        """Create a new dataset from labeled data."""
        logger.info(f"Creating new dataset: {dataset_name}")

        # Load examples from labeled dataset
        examples = self._load_labeled_samples(labeled_dataset_dir)

        if not examples:
            raise ValueError(f"No examples found in {labeled_dataset_dir}")

        # Create dataset
        dataset = self.dataset_repo.create_dataset(
            examples=examples,
            dataset_name=dataset_name,
            metadata={
                "description": f"Law relevancy evaluation dataset created from {labeled_dataset_dir}"
            },
        )

        logger.info(f"Created dataset {dataset.name} with {len(examples)} examples")
        return dataset.id


def get_studio_token() -> str:
    """Get Studio token from environment or configuration."""
    import os

    token = os.environ.get("SERVICE_AUTHENTICATION_TOKEN")
    if not token:
        raise ValueError("SERVICE_AUTHENTICATION_TOKEN environment variable not set")
    return token


if __name__ == "__main__":
    settings = with_settings()

    # Configuration - updated to use evaluation folder structure
    BASE_DIR = Path(__file__).parent.parent
    LABELED_DATASET_DIR = str(BASE_DIR / "labeled_eval_dataset")
    EVALUATION_DATA_DIR = str(BASE_DIR / "intelligence_layer_eval" / "evaluation_data")
    DATASET_NAME = "law_relevancy_dataset"

    logger.info("Starting dataset creation with:")
    logger.info(f"  BASE_DIR: {BASE_DIR}")
    logger.info(f"  LABELED_DATASET_DIR: {LABELED_DATASET_DIR}")
    logger.info(f"  EVALUATION_DATA_DIR: {EVALUATION_DATA_DIR}")
    logger.info(f"  DATASET_NAME: {DATASET_NAME}")

    # Ensure directories exist
    Path(EVALUATION_DATA_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"Created/verified evaluation data directory: {EVALUATION_DATA_DIR}")

    # Create local dataset
    logger.info("Creating FileDatasetRepository...")
    local_dataset_repo = FileDatasetRepository(Path(EVALUATION_DATA_DIR))
    local_dataset_creator = LawRelevancyDatasetCreator(dataset_repo=local_dataset_repo)

    try:
        logger.info("Starting local dataset creation...")
        dataset_local_id = local_dataset_creator.create_dataset(
            dataset_name=DATASET_NAME, labeled_dataset_dir=LABELED_DATASET_DIR
        )
        logger.info(f"Created local dataset with ID: {dataset_local_id}")

        # Create Studio dataset
        logger.info("Creating Studio dataset...")
        studio_token = get_studio_token()
        logger.info("Got Studio token successfully")
        studio_client = StudioClient(
            project="law-monitoring-evaluation",
            create_project=True,
            auth_token=studio_token,
            studio_url=str(settings.pharia_studio_url),
        )
        logger.info("Created Studio client successfully")
        studio_dataset_repo = StudioDatasetRepository(studio_client)
        studio_dataset_creator = LawRelevancyDatasetCreator(
            dataset_repo=studio_dataset_repo
        )

        dataset_studio_id = studio_dataset_creator.create_dataset(
            dataset_name=DATASET_NAME, labeled_dataset_dir=LABELED_DATASET_DIR
        )
        logger.info(f"Created Studio dataset with ID: {dataset_studio_id}")

        # Log clear instructions for running benchmark
        logger.info("=" * 60)
        logger.info("DATASET CREATION COMPLETED")
        logger.info("=" * 60)
        logger.info("To run a benchmark with this dataset, use:")
        logger.info(
            f"uv run intelligence_layer_eval/run_law_relevancy_benchmark.py {dataset_studio_id}"
        )
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error creating datasets: {e}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise
