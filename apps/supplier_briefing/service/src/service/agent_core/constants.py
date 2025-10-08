"""
Shared constants for computed/derived column names and common values.

Use this module for naming of columns created by tools and for canonical
values (e.g., data source labels) that are not raw dataset headers.
"""

import os
import tempfile
from enum import Enum


class AgentMode(Enum):
    """Agent execution modes."""

    AGENT = "agent"
    DETERMINISTIC = "deterministic"


# Data source values
DATA_SOURCE_NHW: str = "Datenerfassung Nicht-Handelsware (NHW)"
DATA_SOURCE_HW: str = "Datenerfassung Handelsware (HW)"

# Repository keys for data storage
REPO_INSIGHTS = "INSIGHTS"
REPO_PANDAS_OBJECTS = "PANDAS_OBJECTS"
REPO_AGENT_RESPONSE = "AGENT_RESPONSE"
REPO_RESULTS = "RESULTS"

LITELLM_CACHE_DIR = os.path.join(
    tempfile.gettempdir(), "litellm_supplier_briefing_cache"
)
LITELLM_CACHE_TTL = 24 * 60 * 60
