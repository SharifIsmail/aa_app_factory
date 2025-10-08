#!/bin/bash
set -eu

# Get the repository root directory
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

files=$(git diff --cached --name-only)
apps=$(echo "$files" | grep '^apps/[^/]\+/ui/' | awk -F/ '{print $2}' | sort -u || true)
shared_frontend=$(echo "$files" | grep '^packages/shared-frontend/' | head -1 || true)

# Check for app UI changes
if [ -n "$apps" ]; then
  echo "Changes in apps UIs: $apps"
  for app in $apps; do
    echo "🎨  Running pnpm format & lint in apps/$app/ui"
    ( cd "apps/$app/ui" \
      && pnpm install --frozen-lockfile --silent \
      && pnpm format \
      && pnpm lint )
  done
fi

# Check for shared-frontend changes
if [ -n "$shared_frontend" ]; then
  echo "Changes in shared-frontend package detected"
  echo "🎨  Running pnpm format & lint in packages/shared-frontend"
  
  cd "packages/shared-frontend"
  
  # Run format and lint (dependencies should already be installed)
  if pnpm format && pnpm lint; then
    echo "✅ Shared-frontend checks passed!"
  else
    echo "❌ Shared-frontend checks failed!"
    exit 1
  fi
  
  cd "$REPO_ROOT"
fi

# If no changes detected
if [ -z "$apps" ] && [ -z "$shared_frontend" ]; then
  echo "No UI changes detected"
fi
