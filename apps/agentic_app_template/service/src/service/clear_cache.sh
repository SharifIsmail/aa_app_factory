#!/bin/bash

# Exit on any error
set -e

# Define cache directories
TEMP_DIR=$(python3 -c "import tempfile; print(tempfile.gettempdir())")
CACHE_DIR="${TEMP_DIR}/lksg_cache"
ARTIFACTS_DIR="${TEMP_DIR}/lksg_artifacts_data"
COMPANY_DATA_DIR="${TEMP_DIR}/lksg_company_data"
LLM_CACHE_DIR="${TEMP_DIR}/agentic_app_cache"
DATA_STORAGE_DIR="${TEMP_DIR}/agentic_app_data_storage"

# Function to check if directory exists and is accessible
check_dir() {
    if [ ! -d "$1" ]; then
        echo "Error: Directory $1 does not exist"
        exit 1
    fi
    if [ ! -w "$1" ]; then
        echo "Error: No write permission for directory $1"
        exit 1
    fi
}

# Check all directories
check_dir "$CACHE_DIR"
check_dir "$ARTIFACTS_DIR"
check_dir "$COMPANY_DATA_DIR"
check_dir "$LLM_CACHE_DIR"
check_dir "$DATA_STORAGE_DIR"

# Remove all files from cache directories
echo "Clearing: lksg_cache"
rm -rf "${CACHE_DIR}"/* || { echo "Error: Failed to clean cache directory"; exit 1; }

echo "Clearing: lksg_artifacts_data"
rm -rf "${ARTIFACTS_DIR}"/* || { echo "Error: Failed to clean artifacts directory"; exit 1; }

echo "Clearing: lksg_company_data"
rm -rf "${COMPANY_DATA_DIR}"/* || { echo "Error: Failed to clean company data directory"; exit 1; }

echo "Clearing: agentic_app_cache"
rm -rf "${LLM_CACHE_DIR}"/* || { echo "Error: Failed to clean LLM cache directory"; exit 1; }

echo "Clearing: agentic_app_data_storage"
rm -rf "${DATA_STORAGE_DIR}"/* || { echo "Error: Failed to clean data storage directory"; exit 1; }

echo "All caches cleared" 
