"""
Shared singleton metaclass implementation following Python best practices.
"""

import threading
from typing import Any, Dict

from loguru import logger


class SingletonMeta(type):
    """Thread-safe singleton metaclass implementation.

    This metaclass ensures that only one instance of a class exists,
    providing thread-safe lazy initialization and testability.

    Usage:
        class MyClass(metaclass=SingletonMeta):
            def __init__(self):
                # Your initialization code here
                pass

    Features:
        - Thread-safe using RLock
        - Lazy initialization (instance created only when needed)
        - Testable with reset_instances() method
        - Works with inheritance
        - No deadlock issues
    """

    _instances: Dict[type, object] = {}
    _lock = threading.RLock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create or return existing singleton instance."""
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    logger.info(f"Creating {cls.__name__} singleton instance")
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def reset_instances(mcs) -> None:
        """Reset all singleton instances (useful for testing).

        This method clears all singleton instances, allowing fresh
        instances to be created. Primarily used for unit testing.
        """
        with mcs._lock:
            logger.info("Resetting all singleton instances")
            mcs._instances.clear()

    @classmethod
    def get_instances(mcs) -> Dict[type, object]:
        """Get all current singleton instances (for debugging/monitoring)."""
        with mcs._lock:
            return mcs._instances.copy()
