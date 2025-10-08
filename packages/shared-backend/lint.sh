#!/bin/sh

set -e

# Detect the current app directory under the repository's "apps" folder
CURRENT_DIR="$PWD"
APP_DIR=""

DIR_TO_CHECK="$CURRENT_DIR"
while [ "$DIR_TO_CHECK" != "/" ]; do
    PARENT_DIR="$(dirname "$DIR_TO_CHECK")"
    GRANDPARENT_DIR="$(dirname "$PARENT_DIR")"
    # Case 1: We are inside apps/<app>/** (parent of parent is 'apps')
    if [ "$(basename "$GRANDPARENT_DIR")" = "apps" ]; then
        APP_DIR="$PARENT_DIR"
        break
    fi
    # Case 2: We are exactly at apps/<app>
    if [ "$(basename "$PARENT_DIR")" = "apps" ]; then
        APP_DIR="$DIR_TO_CHECK"
        break
    fi
    DIR_TO_CHECK="$PARENT_DIR"
done

if [ -z "$APP_DIR" ]; then
    echo "❌ Could not detect an app directory under 'apps/' from: $PWD"
    echo "Run this script from somewhere inside 'apps/<app-name>/**'"
    exit 1
fi

SERVICE_DIR="$APP_DIR/service"

if [ ! -d "$SERVICE_DIR" ]; then
    echo "❌ Service directory not found: $SERVICE_DIR"
    exit 1
fi

echo "📁 Lint scope: $SERVICE_DIR"
cd "$SERVICE_DIR"

if [ "$1" = "check-only" ]; then
    echo "🧹 Checking code format with Ruff (no fixes)..."
    uv run ruff format --diff .
    echo "🔍 Checking linting with Ruff (no fixes)..."
    uv run ruff check .
else
    echo "🧹 Formatting code with Ruff..."
    uv run ruff format .

    echo "🔍 Linting and fixing with Ruff..."
    uv run ruff check . --fix
fi

echo "🔎 Type checking with mypy..."
uv run mypy --install-types --non-interactive .

echo "✅ All checks passed!"


