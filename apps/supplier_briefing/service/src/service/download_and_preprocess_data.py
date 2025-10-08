from loguru import logger

from service.data_preparation import check_output_files_exist, data_preparation
from service.download_raw_data import download_raw_data


def download_and_preprocess_raw_data() -> None:
    if check_output_files_exist():
        logger.info(
            "All processed data files already exist, skipping download and preprocessing"
        )
        return

    # Download raw data from Pharia
    try:
        logger.info("Downloading raw data from Pharia Data during startup...")
        download_raw_data()
        logger.info("Raw data download completed successfully")
    except Exception as e:
        logger.error(f"Failed to download raw data during startup: {e}")
        # Don't fail startup if data download fails - application can still run
        logger.warning("Application will continue without updated raw data")

    # Prepare data
    try:
        logger.info("Preparing data during startup...")
        data_preparation()
        logger.info("Data preparation completed successfully")
    except Exception as e:
        logger.error(f"Failed to prepare data during startup: {e}")
        # Don't fail startup if data preparation fails - application can still run


if __name__ == "__main__":
    download_and_preprocess_raw_data()
