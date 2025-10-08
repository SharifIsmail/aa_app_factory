"""
Configuration for the Intelligence Layer SDK evaluation system.
"""

import os
from pathlib import Path

from loguru import logger

# Base paths - updated for evaluation folder structure
BASE_DIR = Path(__file__).parent.parent.parent  # apps/law_monitoring
SERVICE_DIR = BASE_DIR / "service" / "src"
LABELED_DATASET_DIR = BASE_DIR / "evaluation" / "labeled_eval_dataset"
EVALUATION_DATA_DIR = (
    BASE_DIR / "evaluation" / "intelligence_layer_eval" / "evaluation_data"
)

# Dataset configuration
DATASET_NAME = "law_relevancy_dataset"

# Studio configuration
STUDIO_PROJECT = "law-monitoring-evaluation"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_studio_token() -> str:
    """Get Studio token from environment."""
    token = os.environ.get("SERVICE_AUTHENTICATION_TOKEN")
    if not token:
        raise ValueError("SERVICE_AUTHENTICATION_TOKEN environment variable not set")
    return token


def ensure_directories_exist() -> None:
    """Ensure all required directories exist."""
    EVALUATION_DATA_DIR.mkdir(parents=True, exist_ok=True)
    LABELED_DATASET_DIR.mkdir(parents=True, exist_ok=True)


def print_configuration() -> None:
    """Print current configuration for debugging."""
    logger.info("=== Intelligence Layer SDK Evaluation Configuration ===")
    logger.info(f"Base Directory: {BASE_DIR}")
    logger.info(f"Service Directory: {SERVICE_DIR}")
    logger.info(f"Labeled Dataset Directory: {LABELED_DATASET_DIR}")
    logger.info(f"Evaluation Data Directory: {EVALUATION_DATA_DIR}")
    logger.info(f"Dataset Name: {DATASET_NAME}")
    logger.info(f"Studio Project: {STUDIO_PROJECT}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info("=" * 60)
