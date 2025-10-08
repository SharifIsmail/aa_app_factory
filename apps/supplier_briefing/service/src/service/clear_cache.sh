#!/bin/bash

# Clear LiteLLM disk cache using the dedicated Python script
cd "$(dirname "$0")/../.."
uv run python clear_llm_cache.py
