from pathlib import Path

from loguru import logger

from service.data_preparation import (
    BRUTTO_FILE_EXCEL,
    CONCRETE_FILE_EXCEL,
    RESOURCE_RISKS_EXCEL,
    check_raw_files_exist,
)
from service.raw_data_syncer import RawDataSyncer


def download_raw_data() -> None:
    """Download raw data files from Pharia Data to local storage."""
    if check_raw_files_exist():
        logger.info("All raw data files already exist, skipping download")
        return

    logger.info("Starting raw data download from Pharia Data...")

    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    syncer = RawDataSyncer()
    files_to_download = [
        BRUTTO_FILE_EXCEL,
        CONCRETE_FILE_EXCEL,
        RESOURCE_RISKS_EXCEL,
    ]

    for filename in files_to_download:
        logger.info(f"Downloading {filename} from Pharia Data...")
        syncer.retrieve_data_from_pharia_data(filename)
        logger.info(f"Successfully downloaded {filename}")

    logger.info("Raw data download completed")


if __name__ == "__main__":
    download_raw_data()
