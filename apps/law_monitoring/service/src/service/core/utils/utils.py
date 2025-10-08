"""
General utility functions for the law monitoring application.
"""

import hashlib
from datetime import datetime
from functools import wraps
from typing import Any, Callable


def parse_date_string(date_str: str) -> datetime:
    """
    Parse a date string that can be in various formats.

    Handles both ISO format with time (e.g., "2024-01-15T10:30:00Z")
    and date-only format (e.g., "2024-01-15").

    Args:
        date_str: The date string to parse

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If the date string cannot be parsed
    """
    if "T" in date_str:
        # ISO format with time
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    else:
        # Date only format
        return datetime.strptime(date_str, "%Y-%m-%d")


def generate_url_hash(url: str) -> str:
    """
    Generate a deterministic 32-character hash from a URL.

    This function is used consistently across the application for generating
    file IDs and execution IDs from URLs to ensure uniqueness and consistency.

    Args:
        url: The URL to hash

    Returns:
        A 32-character hexadecimal hash
    """
    # Create SHA256 hash of the URL
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    # Take first 32 characters to keep it manageable while maintaining uniqueness
    return url_hash[:32]


def thread_safe(func: Callable) -> Callable:
    """Decorator to make methods thread-safe by acquiring the instance lock."""

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore
        with self._lock:
            try:
                result = func(self, *args, **kwargs)
                return result
            except Exception:
                raise

    return wrapper
