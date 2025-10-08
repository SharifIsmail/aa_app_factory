#!/bin/bash
set -eu

files=$(git diff --cached --name-only)
apps=$(echo "$files" | grep '^apps/[^/]\+/service/' | awk -F/ '{print $2}' | sort -u)

if [ -n "$apps" ]; then
  echo "Changes in apps services: $apps"
  for app in $apps; do
    script="apps/$app/service/lint.sh"
    if [ -x "$script" ]; then
      echo "🛠  Running $script check-only"
      ( cd "apps/$app/service" && ./lint.sh check-only )
    else
      echo "⚠️  $script not found or not executable"
    fi
  done
else
  echo "No service app changes detected"
fi
