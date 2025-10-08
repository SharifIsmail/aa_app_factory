import base64
import fnmatch
import os
import threading
import time
from typing import List, Optional, Union
from urllib.parse import urljoin

import requests
from loguru import logger

from service.core.utils.singleton import SingletonMeta
from service.core.utils.utils import thread_safe
from service.dependencies import with_settings
from service.law_core.persistence.storage_backend import (
    StorageBackend,
    StorageBackendType,
)


class PhariaDataStorageBackend(StorageBackend, metaclass=SingletonMeta):
    """
    PhariaData implementation of StorageBackend.
    Uses a single PhariaData stage and prefixes filenames with folder names.
    Singleton class to ensure locks work correctly across the application.
    """

    _API_ROUTE = "/api/v1"
    _FOLDER_SEPARATOR = "__"
    _BINARY_MARKER = "PHARIA_DATA_BASE64_BINARY:"

    def __init__(self, base_url: str, token: str | None, stage_name: str) -> None:
        """
        Initialize PhariaData storage backend.
        Sets up PhariaData service with configuration from environment variables.
        """
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        # Initialize PhariaData service components
        self._base_url = base_url
        self._stage_name = stage_name
        self._stages_url = urljoin(base_url, f"{self._API_ROUTE}/stages/")
        self._headers = {"Authorization": f"Bearer {token}"}

        # Cache for the main stage ID
        self._stage_id: str | None = None

        # Thread safety lock - use RLock to allow recursive locking within same thread
        self._lock = threading.RLock()

        # Only initialize stage if this storage backend is actually configured to be used
        settings = with_settings()
        if settings.storage_type in [
            StorageBackendType.PHARIA_DATA.value,
            StorageBackendType.PHARIA_DATA_SYNCED_SQLITE.value,
        ]:
            self._get_or_create_main_stage_id()

        self._initialized = True

        self._file_id_cache: dict[str, str | None] = {}

    def _get_file_id_cached(self, prefixed_filename: str) -> str | None:
        if prefixed_filename in self._file_id_cache:
            return self._file_id_cache[prefixed_filename]

        file_id = self._get_file_id(prefixed_filename)
        self._file_id_cache[prefixed_filename] = file_id
        return file_id

    def _invalidate_file_cache(self, prefixed_filename: str) -> None:
        self._file_id_cache.pop(prefixed_filename, None)

    def _update_file_cache(self, prefixed_filename: str, file_id: str) -> None:
        self._file_id_cache[prefixed_filename] = file_id

    def _validate_folder(self, folder: str) -> None:
        """
        Validate that folder name doesn't contain path separators and is not "empty"".

        Args:
            folder: Folder name to validate

        Raises:
            ValueError: If folder contains invalid characters or is "empty"
        """
        if not folder or folder == "." or folder == "":
            logger.error("Root folder access attempted - not allowed")
            raise ValueError(
                "Root folder access is not allowed. Please specify a valid folder name."
            )

        if "/" in folder or "\\" in folder or "__" in folder:
            logger.error(
                f"Invalid folder name '{folder}' contains forbidden characters"
            )
            raise ValueError(
                f"Folder name '{folder}' cannot contain path separators (/ or \\ or __). "
                "Only simple folder names are supported."
            )

    def _get_or_create_main_stage_id(self) -> str:
        if self._stage_id is not None:
            return self._stage_id

        stage_id = self._get_stage_id()
        if stage_id is None:
            stage_id = self._create_stage()
        else:
            logger.info(
                f"Found existing stage '{self._stage_name}' with ID: {stage_id}"
            )

        self._stage_id = stage_id
        return stage_id

    def _get_stage_id(self) -> str | None:
        page = 1
        page_size = 200

        while True:
            try:
                response = requests.get(
                    self._stages_url,
                    headers=self._headers,
                    params={
                        "name": self._stage_name,
                        "page": str(page),
                        "size": str(page_size),
                    },
                )
                response.raise_for_status()
            except requests.HTTPError as e:
                logger.error(f"Failed to fetch stages page {page}: {e}")
                return None

            data = response.json()
            stages = data.get("stages", [])

            existing_stage = next(
                (stage for stage in stages if stage["name"] == self._stage_name),
                None,
            )

            if existing_stage:
                return str(existing_stage["stageId"])

            if len(stages) < page_size:
                break

            page += 1

        logger.info(f"Stage '{self._stage_name}' not found")
        return None

    def _create_stage(self) -> str:
        logger.info(f"Creating new stage '{self._stage_name}'")
        stage_payload = {"name": self._stage_name}
        try:
            response = requests.post(
                self._stages_url,
                headers=self._headers,
                json=stage_payload,
            )
            response.raise_for_status()
            stage_id = str(response.json()["stageId"])
            logger.info(
                f"Successfully created stage '{self._stage_name}' with ID: {stage_id}"
            )
            return stage_id
        except requests.HTTPError as e:
            logger.error(f"Failed to create stage '{self._stage_name}': {e}")
            raise RuntimeError(f"Failed to create stage '{self._stage_name}': {e}")

    def _get_prefixed_filename(self, folder: str, filename: str) -> str:
        self._validate_folder(folder)
        return f"{folder}{self._FOLDER_SEPARATOR}{filename}"

    def _parse_prefixed_filename(self, prefixed_filename: str) -> tuple[str, str]:
        if self._FOLDER_SEPARATOR not in prefixed_filename:
            return ".", prefixed_filename

        parts = prefixed_filename.split(self._FOLDER_SEPARATOR, 1)
        folder = parts[0]
        filename = parts[1]
        return folder, filename

    def _collect_all_file_records_for_name(
        self, stage_id: str, prefixed_filename: str
    ) -> list[dict]:
        """
        Collect all file records for a given exact name across all pages.

        Returns a list of raw file dictionaries as returned by the API.
        """
        files_url = urljoin(self._stages_url, f"{stage_id}/files")

        all_records: list[dict] = []
        page = 1
        page_size = 200

        while True:
            try:
                response = requests.get(
                    files_url,
                    headers=self._headers,
                    params={
                        "name": prefixed_filename,
                        "page": str(page),
                        "size": str(page_size),
                    },
                )
                response.raise_for_status()
            except requests.HTTPError as e:
                logger.error(
                    f"Failed to fetch files for name '{prefixed_filename}' page {page}: {e}"
                )
                break

            data = response.json()
            page_records = data.get("files", [])

            for record in page_records:
                if record.get("name") == prefixed_filename:
                    all_records.append(record)

            if len(page_records) < page_size:
                break

            page += 1

        return all_records

    def _delete_file_by_id(self, stage_id: str, file_id: str) -> bool:
        """
        Delete a specific file by its identifier. Returns True if deletion succeeded.
        """
        file_url = urljoin(self._stages_url, f"{stage_id}/files/{file_id}")
        try:
            response = requests.delete(file_url, headers=self._headers)
            success = response.status_code == 204
            if not success:
                logger.warning(
                    f"Delete request for fileId={file_id} returned status code {response.status_code}"
                )
            return success
        except requests.HTTPError as e:
            logger.error(f"HTTP error while deleting fileId={file_id}: {e}")
            return False

    def _deduplicate_files_with_same_name(
        self,
        stage_id: str,
        prefixed_filename: str,
        records: Optional[list[dict]] = None,
    ) -> Optional[str]:
        """
        Ensure there is at most one file with the given exact name.

        Keeps one file and deletes the rest. Returns the fileId of the kept file
        when at least one existed; otherwise returns None.
        """
        if records is None:
            records = self._collect_all_file_records_for_name(
                stage_id, prefixed_filename
            )

        if not records:
            logger.info(
                f"No records found for name '{prefixed_filename}' during deduplication"
            )
            return None

        # Choose a deterministic record to keep: keep the first record returned
        # by the API. If the API orders by creation time, this will be stable.
        record_to_keep = records[0]
        keep_id = str(record_to_keep.get("fileId"))

        # Delete all other duplicates
        for record in records[1:]:
            duplicate_id = str(record.get("fileId"))
            if duplicate_id == keep_id:
                # Defensive: skip if somehow identical
                continue
            deleted = self._delete_file_by_id(stage_id, duplicate_id)
            if deleted:
                logger.info(
                    f"Deleted duplicate file for name '{prefixed_filename}' (fileId={duplicate_id})"
                )
            else:
                logger.warning(
                    f"Failed to delete duplicate file for name '{prefixed_filename}' (fileId={duplicate_id})"
                )

        # Invalidate cache so future lookups reflect the deduplicated state
        self._invalidate_file_cache(prefixed_filename)

        return keep_id

    def _get_file_id(self, prefixed_filename: str) -> Optional[str]:
        stage_id = self._get_or_create_main_stage_id()
        records = self._collect_all_file_records_for_name(stage_id, prefixed_filename)

        if not records:
            logger.debug(f"File '{prefixed_filename}' not found")
            return None

        if len(records) > 1:
            logger.warning(
                f"Detected duplicate files for name '{prefixed_filename}'. Attempting to deduplicate."
            )
            return self._deduplicate_files_with_same_name(
                stage_id, prefixed_filename, records=records
            )

        return str(records[0]["fileId"])

    @thread_safe
    def save_file(self, folder: str, filename: str, content: Union[str, bytes]) -> str:
        """
        Save (upsert) content to PhariaData storage.
        If a file with the same name already exists, it will be updated via PUT;
        If not, we create it via POST.

        Binary content is automatically encoded as base64 for storage.

        Args:
            folder: Folder where to save the file (simple name, NO path separators)
            filename: Name of the file (without path)
            content: Content to save (string or bytes)

        Returns:
            PhariaData file identifier where the file was saved
        """
        logger.info(f"Saving file '{filename}' to folder '{folder}'")

        stage_id = self._get_or_create_main_stage_id()
        files_url = urljoin(self._stages_url, f"{stage_id}/files")
        prefixed_filename = self._get_prefixed_filename(folder, filename)

        # Handle binary vs text content
        if isinstance(content, bytes):
            # Encode binary content as base64 with marker
            encoded_content = base64.b64encode(content).decode("utf-8")
            file_content = f"{self._BINARY_MARKER}{encoded_content}"
            content_type = "text/plain"
            logger.debug(
                f"Encoded binary content for '{filename}' as base64 ({len(content)} bytes -> {len(file_content)} chars)"
            )
        else:
            # Store text content as-is
            file_content = content
            content_type = "text/plain; charset=utf-8"

        existing_id = self._get_file_id_cached(prefixed_filename)
        if existing_id:
            put_url = urljoin(self._stages_url, f"{stage_id}/files/{existing_id}")

            put_files = {
                "sourceData": (
                    prefixed_filename,
                    file_content.encode("utf-8"),
                    content_type,
                )
            }

            headers = {
                k: v for k, v in self._headers.items() if k.lower() != "content-type"
            }

            try:
                response = requests.put(put_url, headers=headers, files=put_files)
                response.raise_for_status()
                file_id = str(response.json()["fileId"])
                if file_id != existing_id:
                    raise AssertionError(
                        f"File ID mismatch after updating file via PUT: expected {existing_id}, got {file_id}"
                    )
                return file_id
            except requests.HTTPError as e:
                raise RuntimeError(
                    f"PUT failed for '{prefixed_filename}' (fileId={existing_id}): {e}."
                )

        data = {"name": prefixed_filename}

        post_files = {
            "sourceData": (
                prefixed_filename,
                file_content.encode("utf-8"),
                content_type,
            )
        }
        try:
            response = requests.post(
                files_url, headers=self._headers, files=post_files, data=data
            )
            response.raise_for_status()
            file_id = str(response.json()["fileId"])
            self._update_file_cache(prefixed_filename, file_id)
            return file_id
        except requests.HTTPError as e:
            logger.error(f"Failed to save '{prefixed_filename}' via POST: {e}")
            raise RuntimeError(
                f"Failed to save file '{filename}' to folder '{folder}': {e}"
            )

    @thread_safe
    def load_file(self, folder: str, filename: str) -> Optional[Union[str, bytes]]:
        """
        Load content from PhariaData storage.

        Automatically detects and decodes base64-encoded binary content.

        Args:
            folder: Folder containing the file (simple name, NO path separators)
            filename: Name of the file (without path)

        Returns:
            File content if exists (str or bytes depending on original type), None otherwise
        """
        prefixed_filename = self._get_prefixed_filename(folder, filename)
        file_id = self._get_file_id_cached(prefixed_filename)

        if file_id is None:
            logger.info(f"File '{filename}' not found in folder '{folder}'")
            return None

        stage_id = self._get_or_create_main_stage_id()
        file_url = urljoin(self._stages_url, f"{stage_id}/files/{file_id}")

        try:
            response = requests.get(file_url, headers=self._headers)
            response.raise_for_status()
            response.encoding = "utf-8"
            content = response.text

            # Check if content is base64-encoded binary
            if content.startswith(self._BINARY_MARKER):
                # Remove marker and decode base64
                encoded_content = content[len(self._BINARY_MARKER) :]
                try:
                    decoded_bytes = base64.b64decode(encoded_content)
                    logger.debug(
                        f"Decoded base64 content for '{filename}' ({len(content)} chars -> {len(decoded_bytes)} bytes)"
                    )
                    return decoded_bytes
                except Exception as e:
                    logger.error(
                        f"Failed to decode base64 content for '{filename}': {e}"
                    )
                    raise ValueError(
                        f"Failed to decode base64 content for file '{filename}' in folder '{folder}': {e}"
                    ) from e
            else:
                # Return text content as-is
                return content

        except requests.HTTPError as e:
            logger.error(
                f"Failed to load file '{filename}' from folder '{folder}': {e}"
            )
            return None

    @thread_safe
    def file_exists(self, folder: str, filename: str) -> bool:
        """
        Check if a file exists in PhariaData storage.

        Args:
            folder: Folder to check (simple name, NO path separators)
            filename: Name of the file (without path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            prefixed_filename = self._get_prefixed_filename(folder, filename)
            return self._get_file_id_cached(prefixed_filename) is not None
        except Exception as e:
            logger.error(
                f"Error checking if file '{filename}' exists in folder '{folder}': {e}"
            )
            return False

    @thread_safe
    def list_files(self, folder: str, pattern: Optional[str] = None) -> List[str]:
        """
        List files in PhariaData storage folder.

        Args:
            folder: Folder to list files from (simple name, NO path separators)
            pattern: Optional glob pattern to filter files

        Returns:
            List of filenames (without folder path)
        """
        self._validate_folder(folder)  # Reject root folder access

        stage_id = self._get_or_create_main_stage_id()
        files_url = urljoin(self._stages_url, f"{stage_id}/files")

        # Create prefix for this folder
        folder_prefix = f"{folder}{self._FOLDER_SEPARATOR}"

        filenames = []
        page = 1
        page_size = 200

        while True:
            try:
                response = requests.get(
                    files_url,
                    headers=self._headers,
                    params={"page": str(page), "size": str(page_size)},
                )
                response.raise_for_status()
            except requests.HTTPError as e:
                logger.error(
                    f"Failed to fetch files page {page} for folder '{folder}': {e}"
                )
                return []

            data = response.json()
            files = data.get("files", [])

            for file in files:
                filename = file["name"]
                if filename is None:
                    logger.warning(
                        f"No filename for file {file}, skipping corrupted file. This should not happen. Make sure every file created has a filename."
                    )
                    continue
                if filename.startswith(folder_prefix):
                    filename_without_prefix = filename[len(folder_prefix) :]
                    if filename_without_prefix in filenames:
                        # Be resilient to duplicates: log and skip additional occurrences
                        logger.warning(
                            f"Duplicate filename '{filename_without_prefix}' detected in folder '{folder}'. Keeping one occurrence."
                        )
                        continue
                    filenames.append(filename_without_prefix)

            if len(files) < page_size:
                break

            page += 1

        if pattern:
            filenames = [name for name in filenames if fnmatch.fnmatch(name, pattern)]

        return filenames

    @thread_safe
    def delete_file(self, folder: str, filename: str) -> bool:
        """
        Delete a file from PhariaData storage.

        Args:
            folder: Folder containing the file (simple name, NO path separators)
            filename: Name of the file (without path)

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            prefixed_filename = self._get_prefixed_filename(folder, filename)
            file_id = self._get_file_id_cached(prefixed_filename)

            if file_id is None:
                logger.info(
                    f"File '{filename}' not found in folder '{folder}', nothing to delete"
                )
                return False

            stage_id = self._get_or_create_main_stage_id()
            file_url = urljoin(self._stages_url, f"{stage_id}/files/{file_id}")

            response = requests.delete(file_url, headers=self._headers)
            success = response.status_code == 204

            if success:
                self._invalidate_file_cache(prefixed_filename)
                logger.info(
                    f"Successfully deleted file '{filename}' from folder '{folder}'"
                )
            else:
                logger.warning(
                    f"Delete request for file '{filename}' returned status code {response.status_code}"
                )

            return success
        except Exception as e:
            logger.error(
                f"Error deleting file '{filename}' from folder '{folder}': {e}"
            )
            return False

    @thread_safe
    def list_folders(self) -> List[str]:
        """
        List all folders in PhariaData storage.
        Extracts unique folder prefixes from all filenames.

        Returns:
            List of folder names
        """
        try:
            stage_id = self._get_or_create_main_stage_id()
            files_url = urljoin(self._stages_url, f"{stage_id}/files")

            folders: set[str] = set()
            page = 1
            page_size = 200

            while True:
                try:
                    response = requests.get(
                        files_url,
                        headers=self._headers,
                        params={"page": str(page), "size": str(page_size)},
                    )
                    response.raise_for_status()
                except requests.HTTPError as e:
                    logger.error(
                        f"Failed to fetch files page {page} for folder discovery: {e}"
                    )
                    break

                data = response.json()
                files = data.get("files", [])

                for file in files:
                    filename = file.get("name")
                    if filename is None:
                        logger.warning(f"Skipping file with no name: {file}")
                        continue

                    if self._FOLDER_SEPARATOR in filename:
                        folder_name = filename.split(self._FOLDER_SEPARATOR, 1)[0]
                        folders.add(folder_name)

                if len(files) < page_size:
                    break

                page += 1

            folder_list = sorted(list(folders))
            return folder_list

        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            return []

    @thread_safe
    def create_folder(self, folder: str) -> bool:
        """
        Always returns true, as folder structure is handled manually.
        """
        return True

    @thread_safe
    def get_files_in_folder(self, folder: str) -> List[str]:
        """
        Get all files in a specific folder in PhariaData storage.
        Same as list_files without pattern filtering.

        Args:
            folder: Folder to get files from (simple name, NO path separators)

        Returns:
            List of filenames (without folder path)
        """
        self._validate_folder(folder)
        return self.list_files(folder)

    @thread_safe
    def validate_connection(self) -> None:
        """Validate that the storage backend is properly configured and accessible."""
        try:
            # Test stage access
            stage_id = self._get_or_create_main_stage_id()

            # Test basic operations
            test_folder = "_connection_test"
            test_filename = "validation.txt"
            test_content = f"Connection test at {time.time()}"

            # Test full CRUD cycle
            self.save_file(test_folder, test_filename, test_content)

            if not self.file_exists(test_folder, test_filename):
                raise RuntimeError("File existence check failed")

            loaded_content = self.load_file(test_folder, test_filename)
            if loaded_content != test_content:
                raise RuntimeError("Content verification failed")

            files = self.list_files(test_folder)
            if test_filename not in files:
                raise RuntimeError("File listing failed")

            if not self.delete_file(test_folder, test_filename):
                raise RuntimeError("File deletion failed")

            logger.info(
                f"PhariaData storage validation successful (stage_id: {stage_id})"
            )

        except Exception as e:
            logger.error(f"PhariaData storage validation failed: {e}")
            raise


# Singleton instance should be created by the application with proper parameters
settings = with_settings()
pharia_data_storage_backend = PhariaDataStorageBackend(
    str(settings.pharia_data_url),
    os.environ.get("SERVICE_AUTHENTICATION_TOKEN"),
    settings.pharia_data_stage_name,
)
