#!/usr/bin/env python3

"""
This script clears the cache of the law monitoring system.
It clears the CacheService database cache and the temp directories.
It also opens the temp folder in Finder.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from loguru import logger

from service.law_core.persistence.cache_service import cache_service


def clear_temp_directories() -> List[str]:
    """Clear law monitoring related directories from temp folder."""
    temp_dir = Path(tempfile.gettempdir())

    # Directories to clean
    dirs_to_clean = [
        "law_monitoring_cache",
        "law_monitoring_data_storage",
        "law_data_service_locks",
        "law_monitoring_locks",
    ]

    cleaned_dirs: List[str] = []
    for dir_name in dirs_to_clean:
        dir_path = temp_dir / dir_name
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                cleaned_dirs.append(str(dir_path))
                logger.info(f"✓ Removed directory: {dir_path}")
            except Exception as e:
                logger.error(f"✗ Failed to remove {dir_path}: {e}")

    if not cleaned_dirs:
        logger.info("✓ No temp directories found to clean")

    return cleaned_dirs


def open_temp_folder_in_finder() -> None:
    """Open the temp directory in Finder (macOS only)."""
    temp_dir = tempfile.gettempdir()
    try:
        subprocess.run(["open", temp_dir], check=True)
        logger.info(f"✓ Opened temp folder in Finder: {temp_dir}")
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to open Finder: {e}")
    except FileNotFoundError:
        logger.warning("✗ 'open' command not found (not running on macOS?)")


def main() -> None:
    """Clear cache using CacheService and clean temp directories."""
    logger.info("=== Law Monitoring Cache Cleanup ===")

    # Clear CacheService database cache
    logger.info("\n1. Clearing CacheService database cache...")
    cache_service.clear_cache()
    logger.info("✓ CacheService cache cleared successfully!")

    # Clear temp directories
    logger.info("\n2. Cleaning temp directories...")
    clear_temp_directories()

    # Open temp folder in Finder
    logger.info("\n3. Opening temp folder in Finder...")
    open_temp_folder_in_finder()

    logger.info("\n✓ Cache cleanup completed!")


if __name__ == "__main__":
    main()
