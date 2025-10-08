#!/bin/sh

set -e

# Delegate to the shared linter. Running this script from anywhere under the app will scope to this app's service dir.
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO_ROOT" ]; then
    # Fallback: assume this file is two levels under repo root: apps/<app>/service
    REPO_ROOT="$(cd "$(dirname "$0")"/../../.. && pwd)"
fi

exec sh "$REPO_ROOT/packages/shared-backend/lint.sh" "$@"
