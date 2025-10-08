import hashlib
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional


class PersistenceService:
    """
    Central service responsible for all data persistence related operations including:
    - Caching data
    - Saving files to disk (XML, HTML, etc.)
    - Managing temporary and permanent storage locations
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls) -> "PersistenceService":
        """Get or create the singleton instance of PersistenceService."""
        if cls._instance is None:
            cls._instance = PersistenceService()
        return cls._instance

    def __init__(self) -> None:
        if PersistenceService._instance is not None:
            return

        self.temp_dir = tempfile.gettempdir()
        self.cache_dir = os.path.join(self.temp_dir, "agentic_app_cache")
        self.data_storage_dir = self._ensure_data_storage_dir()

        # Ensure directories exist
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.data_storage_dir, exist_ok=True)

        # Set self as the instance
        PersistenceService._instance = self

    # ============= Internal Helper Methods =============

    def _ensure_data_storage_dir(self) -> Path:
        """Create and return the data storage directory."""
        data_storage_dir = Path(tempfile.gettempdir()) / "agentic_app_data_storage"
        data_storage_dir.mkdir(parents=True, exist_ok=True)
        return data_storage_dir

    def _generate_cache_filename(self, cache_id: str) -> str:
        """Generate a hashed filename for a cache ID."""
        hash_object = hashlib.sha256(cache_id.encode())
        filename = hash_object.hexdigest() + ".json"
        return filename

    def _save_file(self, content: str, filepath: str, ensure_dir: bool = True) -> str:
        """
        Generic method to save content to a file.

        Args:
            content: Content to save
            filepath: Path where to save the file
            ensure_dir: Whether to ensure the directory exists

        Returns:
            Absolute path to the saved file
        """
        if ensure_dir:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return os.path.abspath(filepath)

    def _load_file(self, filepath: str) -> Optional[str]:
        """
        Generic method to load content from a file.

        Args:
            filepath: Path of the file to load

        Returns:
            File content if the file exists, None otherwise
        """
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def _file_exists(self, filepath: str) -> bool:
        """
        Check if a file exists.

        Args:
            filepath: Path of the file to check

        Returns:
            True if the file exists, False otherwise
        """
        return os.path.exists(filepath)

    def _list_files(self, directory: str, pattern: Optional[str] = None) -> list:
        """
        List files in a directory, optionally filtering by pattern.

        Args:
            directory: Directory to list files from
            pattern: Optional glob pattern to filter files

        Returns:
            List of file paths
        """
        if not os.path.exists(directory):
            return []

        if pattern:
            import glob

            return glob.glob(os.path.join(directory, pattern))

        return [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]

    def _xml_to_dict(self, element: ET.Element) -> dict[str, Any]:
        """
        Convert an XML element to a dictionary recursively.

        Args:
            element: XML element to convert

        Returns:
            Dictionary representation of the XML
        """
        result: dict[str, Any] = {}

        # Process attributes
        for key, value in element.attrib.items():
            result[key] = value

        # Process text content if present and not just whitespace
        if element.text and element.text.strip():
            text = element.text.strip()
            # Don't include placeholder text from template
            if text.startswith("[") and text.endswith("]"):
                pass
            else:
                result["value"] = text

        # Process children
        for child in element:
            child_data = self._xml_to_dict(child)

            # Handle multiple children with the same tag
            if child.tag in result:
                # If this tag appears more than once, ensure it becomes a list
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result

    # ============= Public Methods =============

    def load_from_cache(self, cache_id: str) -> Optional[Any]:
        """
        Load data from cache using the given cache ID.

        Args:
            cache_id: The identifier for the cached data

        Returns:
            The cached data if it exists, None otherwise
        """
        filename = self._generate_cache_filename(cache_id)
        cache_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                return json.load(f)
        return None

    def save_to_cache(self, cache_id: str, data: Any) -> str:
        """
        Save data to cache with the given cache ID.

        Args:
            cache_id: The identifier for the cached data
            data: The data to cache

        Returns:
            The path where the data was cached
        """
        filename = self._generate_cache_filename(cache_id)
        cache_path = os.path.join(self.cache_dir, filename)
        with open(cache_path, "w") as f:
            json.dump(data, f)
        return cache_path

    def save_xml(self, content: str, filename: str) -> str:
        """
        Save XML content to the data storage directory.

        Args:
            content: XML content to save
            filename: Name for the XML file (without extension)

        Returns:
            The path where the XML was saved
        """
        filepath = str(self.data_storage_dir / f"{filename}.xml")
        return self._save_file(content, filepath)

    def save_html_report(self, content: str, filename: str) -> str:
        """
        Save HTML report content to the data storage directory.

        Args:
            content: HTML content to save
            filename: Name for the HTML file (without extension)

        Returns:
            Absolute path to the saved file
        """
        filepath = os.path.join(self.data_storage_dir, f"{filename}.html")
        return self._save_file(content, filepath)

    def list_cached_agentic_data(self) -> list:
        """
        List all agentic XML files in the data storage directory and parse their content.

        Returns:
            List of dictionaries containing agentic data from get_agentic_data_by_uuid

        Raises:
            Exception: If any XML file cannot be parsed
        """
        xml_files = self._list_files(str(self.data_storage_dir), "*.xml")
        results = []

        for xml_file in xml_files:
            filename = os.path.splitext(os.path.basename(xml_file))[0]

            # Remove _research suffix if present (to get the base UUID)
            uuid = filename
            if filename.endswith("_research"):
                uuid = filename[:-9]
                agentic_info = self.get_agentic_data_by_uuid(uuid)
                if agentic_info is not None:
                    results.append(agentic_info)

        return results

    def get_agentic_data_by_uuid(self, uuid: str) -> dict[str, Any] | None:
        """
        Load and parse agentic data XML file based on UUID.

        Args:
            uuid: UUID of the agentic data file (without extension)

        Returns:
            Dictionary containing:
            - uuid: UUID of the agentic data
            - name: Name extracted from XML (falls back to UUID if not found)
            - path: Full path to the XML file
            - data: Parsed XML data as a dictionary
            - agentic_data_report_path: Full path to HTML report if it exists, None otherwise

        Raises:
            FileNotFoundError: If no matching XML file is found
            ET.ParseError: If the XML cannot be parsed
            Exception: For any other parsing issues
        """
        try:
            xml_path = os.path.join(str(self.data_storage_dir), f"{uuid}_research.xml")

            if not self._file_exists(xml_path):
                raise FileNotFoundError(f"No XML file found for UUID: {uuid}")

            xml_content = self._load_file(xml_path)
            if not xml_content:
                raise FileNotFoundError(f"XML file exists but is empty: {xml_path}")

            root = ET.fromstring(xml_content)

            agentic_info: dict[str, Any] = {
                "uuid": uuid,
                "path": xml_path,
                "data": self._xml_to_dict(root),
                "name": uuid,  # Simply use UUID as the name
            }

            agentic_data_report_path = os.path.join(
                self.data_storage_dir, f"{uuid}_agentic_report.html"
            )
            agentic_info["agentic_data_report_path"] = (
                os.path.abspath(agentic_data_report_path)
                if self._file_exists(agentic_data_report_path)
                else None
            )

            return agentic_info
        except Exception:
            import traceback

            print(f"Error processing agentic data with UUID {uuid}:")
            print(traceback.format_exc())
            return None

    def load_and_store_html_report(
        self, source_folder: str, source_filename: str, target_filename: str
    ) -> str:
        """
        Load an HTML report from a source folder and store it in the data storage directory.

        Args:
            source_folder: Path to the source folder containing the HTML report
            source_filename: Name of the source HTML file (with extension)
            target_filename: Name to save the file as (without extension)

        Returns:
            Absolute path to the stored file

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        print(
            f"Loading and storing HTML report: {source_filename} -> {target_filename}"
        )
        source_path = os.path.join(source_folder, source_filename)
        if not self._file_exists(source_path):
            raise FileNotFoundError(f"Source HTML file not found: {source_path}")

        content = self._load_file(source_path)
        if not content:
            raise FileNotFoundError(f"Source HTML file is empty: {source_path}")

        return self.save_html_report(content, target_filename)

    def load_and_store_xml_report(
        self, source_folder: str, source_filename: str, target_filename: str
    ) -> str:
        """
        Load an XML report from a source folder and store it in the data storage directory.

        Args:
            source_folder: Path to the source folder containing the XML report
            source_filename: Name of the source XML file (with extension)
            target_filename: Name to save the file as (without extension)

        Returns:
            Absolute path to the stored file

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        print(f"Loading and storing XML report: {source_filename} -> {target_filename}")
        source_path = os.path.join(source_folder, source_filename)
        if not self._file_exists(source_path):
            raise FileNotFoundError(f"Source XML file not found: {source_path}")

        content = self._load_file(source_path)
        if not content:
            raise FileNotFoundError(f"Source XML file is empty: {source_path}")

        return self.save_xml(content, target_filename)


# Create a singleton instance to be imported
persistence_service = PersistenceService.get_instance()
