#!/bin/bash


SOURCE_DIR=$1
TARGET_DIR=$2

if [ -z "$SOURCE_DIR" ] || [ -z "$TARGET_DIR" ]; then
  echo "Usage: ./new_app.sh <source_dir> <target_dir>"
  exit 1
fi

echo "Copying project from $SOURCE_DIR to $TARGET_DIR..."

rsync -av --progress "$SOURCE_DIR"/ "$TARGET_DIR"/ \
  --exclude ".venv" \
  --exclude "node_modules" \
  --exclude "__pycache__" \
  --exclude ".mypy_cache" \
  --exclude ".pytest_cache" \
  --exclude ".ruff_cache" \
  --exclude "dist" \
  --exclude "build" \
  --exclude "*.egg-info" \
  --exclude ".DS_Store" \
  --exclude ".env" \
  --exclude ".coverage" \
  --exclude ".vscode" \
  --exclude ".idea" \
  --exclude "*.log"

echo "Cleaning any leftover symlinks to old environments..."
find "$TARGET_DIR" -type l -exec rm -v {} \; 2>/dev/null

echo "Removing .git if exists (for fresh start)..."
rm -rf "$TARGET_DIR/.git"

mkdir -p "$TARGET_DIR/service/src/service/ui-artifacts"


echo "✅ Done. '$TARGET_DIR' is ready for a fresh environment!"
