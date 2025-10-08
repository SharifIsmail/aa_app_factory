#!/bin/bash

# Get the temp directory (macOS specific)
TEMP_DIR=$(echo $TMPDIR)
if [ -z "$TEMP_DIR" ]; then
    TEMP_DIR="/tmp"
fi

CACHE_DIR="$TEMP_DIR/lksg_cache"

# Check if cache directory exists
if [ -d "$CACHE_DIR" ]; then
    echo "Deleting cache directory: $CACHE_DIR"
    rm -rf "$CACHE_DIR"
    if [ $? -eq 0 ]; then
        echo "Cache directory deleted successfully"
    else
        echo "Error: Failed to delete cache directory"
        exit 1
    fi
else
    echo "Cache directory does not exist: $CACHE_DIR"
fi 