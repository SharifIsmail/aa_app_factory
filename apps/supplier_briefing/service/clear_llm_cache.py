#!/usr/bin/env python3
"""
Clear LiteLLM disk cache.
"""

import os
import shutil

from service.agent_core.constants import LITELLM_CACHE_DIR


def main() -> None:
    """Clear the LiteLLM disk cache."""
    shutil.rmtree(LITELLM_CACHE_DIR, ignore_errors=True)
    os.makedirs(LITELLM_CACHE_DIR, exist_ok=True)


if __name__ == "__main__":
    main()
