"""
Factory module for creating storage backend instances.
"""

from service.dependencies import with_settings
from service.law_core.persistence.filesystem_storage_backend import (
    filesystem_storage_backend,
)
from service.law_core.persistence.pharia_data_storage_backend import (
    pharia_data_storage_backend,
)
from service.law_core.persistence.pharia_data_synced_sqlite_storage_backend import (
    pharia_data_synced_sqlite_storage_backend,
)
from service.law_core.persistence.storage_backend import (
    StorageBackend,
    StorageBackendType,
)

_STORAGE_BACKENDS = {
    StorageBackendType.FILESYSTEM: filesystem_storage_backend,
    StorageBackendType.PHARIA_DATA: pharia_data_storage_backend,
    StorageBackendType.PHARIA_DATA_SYNCED_SQLITE: pharia_data_synced_sqlite_storage_backend,
}


def fetch_storage_backend_instance(
    storage_backend_type: StorageBackendType,
) -> StorageBackend:
    """
    Fetch the specified storage backend singleton instance.

    Args:
        storage_backend_type: The type of storage backend to fetch

    Returns:
        Singleton instance of the specified storage backend

    Raises:
        ValueError: If the storage backend type is not implemented
    """

    if storage_backend_type not in _STORAGE_BACKENDS:
        available_types = list(_STORAGE_BACKENDS.keys())
        raise ValueError(
            f"Storage backend type {storage_backend_type} is not implemented. "
            f"Available types: {available_types}"
        )

    return _STORAGE_BACKENDS[storage_backend_type]


def get_configured_storage_backend() -> StorageBackend:
    """
    Get the storage backend instance configured in settings.

    Returns:
        Singleton instance of the configured storage backend

    Raises:
        ValueError: If the configured storage backend type is not implemented
    """

    settings = with_settings()
    storage_type = StorageBackendType(settings.storage_type)

    return fetch_storage_backend_instance(storage_type)
