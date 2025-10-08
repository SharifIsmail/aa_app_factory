"""
Default configurations module for law monitoring system.

This module provides default company and team configurations that ensure
the system remains functional even after fresh deployments when dynamic
configuration may be lost.
"""

from .default_company_config import (
    get_default_company_config,
    get_default_company_description,
    get_default_teams,
)

__all__ = [
    "get_default_company_config",
    "get_default_company_description",
    "get_default_teams",
]
