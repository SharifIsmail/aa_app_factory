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
        # Only initialize if this is not a duplicate instance
        if PersistenceService._instance is not None:
            return

        # Set up standard directories
        self.temp_dir = tempfile.gettempdir()
        self.cache_dir = os.path.join(self.temp_dir, "lksg_cache")
        self.artifacts_dir = os.path.join(self.temp_dir, "lksg_artifacts_data")
        self.company_data_dir = self._ensure_company_data_dir()

        # Ensure directories exist
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)

        # Set self as the instance
        PersistenceService._instance = self

    def _ensure_company_data_dir(self) -> Path:
        """Create and return the company data directory."""
        company_data_dir = Path(tempfile.gettempdir()) / "lksg_company_data"
        company_data_dir.mkdir(parents=True, exist_ok=True)
        return company_data_dir

    def _generate_cache_filename(self, cache_id: str) -> str:
        """Generate a hashed filename for a cache ID."""
        hash_object = hashlib.sha256(cache_id.encode())
        filename = hash_object.hexdigest() + ".json"
        return filename

    # ============= Cache Operations =============

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

    def clear_cache(self, cache_id: Optional[str] = None) -> None:
        """
        Clear cache entries.

        Args:
            cache_id: If provided, only clear this specific cache entry.
                     If None, clear all cache.
        """
        if cache_id:
            filename = self._generate_cache_filename(cache_id)
            cache_path = os.path.join(self.cache_dir, filename)
            if os.path.exists(cache_path):
                os.remove(cache_path)
        else:
            # Clear all cache files
            for file in os.listdir(self.cache_dir):
                if file.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, file))

    def cache_exists(self, cache_id: str) -> bool:
        """
        Check if a cache entry exists.

        Args:
            cache_id: The identifier for the cached data

        Returns:
            True if the cache exists, False otherwise
        """
        filename = self._generate_cache_filename(cache_id)
        cache_path = os.path.join(self.cache_dir, filename)
        return os.path.exists(cache_path)

    # ============= File Operations =============

    def save_file(self, content: str, filepath: str, ensure_dir: bool = True) -> str:
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

    def load_file(self, filepath: str) -> Optional[str]:
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

    def file_exists(self, filepath: str) -> bool:
        """
        Check if a file exists.

        Args:
            filepath: Path of the file to check

        Returns:
            True if the file exists, False otherwise
        """
        return os.path.exists(filepath)

    # ============= Specific File Type Operations =============

    def save_xml(self, content: str, filename: str) -> str:
        """
        Save XML content to the company data directory.

        Args:
            content: XML content to save
            filename: Name for the XML file (without extension)

        Returns:
            The path where the XML was saved
        """
        filepath = str(self.company_data_dir / f"{filename}.xml")
        return self.save_file(content, filepath)

    def load_xml(self, filename: str) -> Optional[str]:
        """
        Load XML content from the company data directory.

        Args:
            filename: Name of the XML file (without extension)

        Returns:
            XML content if found, None otherwise
        """
        filepath = str(self.company_data_dir / f"{filename}.xml")
        return self.load_file(filepath)

    def save_html_report(self, content: str, filename: str) -> str:
        """
        Save HTML report content to the artifacts directory.

        Args:
            content: HTML content to save
            filename: Name for the HTML file (without extension)

        Returns:
            Absolute path to the saved file
        """
        filepath = os.path.join(self.artifacts_dir, f"{filename}.html")
        return self.save_file(content, filepath)

    # ============= Directory Operations =============

    def list_files(self, directory: str, pattern: Optional[str] = None) -> list:
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

    def list_cached_companies(self) -> list:
        """
        List all company XML files in the company_data_dir and parse their content.

        Returns:
            List of dictionaries containing company data from get_company_data_by_uuid

        Raises:
            Exception: If any XML file cannot be parsed
        """
        xml_files = self.list_files(str(self.company_data_dir), "*.xml")
        results = []

        for xml_file in xml_files:
            filename = os.path.splitext(os.path.basename(xml_file))[0]

            # Remove _data suffix if present (to get the base UUID)
            uuid = filename
            if filename.endswith("_data"):
                uuid = filename[:-5]
                company_info = self.get_company_data_by_uuid(uuid)
                if company_info is not None:
                    results.append(company_info)

        return results

    def fetch_cached_company_by_name(self, company_name: str) -> Optional[dict]:
        """
        Find a company by name in the cached company data.

        Args:
            company_name: The name of the company to find (case-insensitive)

        Returns:
            Company data dictionary if found, None otherwise
        """
        companies = self.list_cached_companies()

        for company in companies:
            if company["name"].lower() == company_name.lower():
                return company

        return None

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

    def list_html_reports(self) -> list:
        """
        List all HTML reports in the artifacts_dir.

        Returns:
            List of report filenames (without extension)
        """
        html_files = self.list_files(self.artifacts_dir, "*.html")
        return [os.path.splitext(os.path.basename(f))[0] for f in html_files]

    def get_company_data_by_uuid(self, uuid: str) -> dict[str, Any] | None:
        """
        Load and parse company data XML file based on UUID.

        Args:
            uuid: UUID of the company data file (without extension)

        Returns:
            Dictionary containing:
            - uuid: UUID of the company
            - name: Company name extracted from XML (falls back to UUID if not found)
            - path: Full path to the XML file
            - data: Parsed XML data as a dictionary
            - company_data_report_path: Full path to HTML report if it exists, None otherwise
            - risks_report_path: Full path to risk HTML report if it exists, None otherwise

        Raises:
            FileNotFoundError: If no matching XML file is found
            ET.ParseError: If the XML cannot be parsed
            Exception: For any other parsing issues
        """
        try:
            xml_path = os.path.join(str(self.company_data_dir), f"{uuid}_data.xml")

            if not self.file_exists(xml_path):
                raise FileNotFoundError(f"No XML file found for UUID: {uuid}")

            xml_content = self.load_file(xml_path)
            if not xml_content:
                raise FileNotFoundError(f"XML file exists but is empty: {xml_path}")

            root = ET.fromstring(xml_content)

            company_info: dict[str, Any] = {
                "uuid": uuid,
                "path": xml_path,
                "data": self._xml_to_dict(root),
            }

            # Extract company name from XML structure
            name_element = root.find(".//CompanyIdentity/Name/FinalApprovedName")
            if name_element is not None and name_element.text:
                company_name = name_element.text
                if company_name != "[Insert final validated company name here]":
                    company_info["name"] = company_name
                else:
                    company_info["name"] = uuid
            else:
                company_info["name"] = uuid

            company_data_report_path = os.path.join(
                self.artifacts_dir, f"{uuid}_company_data_report.html"
            )
            company_info["company_data_report_path"] = (
                os.path.abspath(company_data_report_path)
                if self.file_exists(company_data_report_path)
                else None
            )

            risks_report_path = os.path.join(
                self.artifacts_dir, f"{uuid}_risks_report.html"
            )
            company_info["risks_report_path"] = (
                os.path.abspath(risks_report_path)
                if self.file_exists(risks_report_path)
                else None
            )

            return company_info
        except Exception:
            import traceback

            print(f"Error processing company with UUID {uuid}:")
            print(traceback.format_exc())
            return None

    def load_and_store_html_report(
        self, source_folder: str, source_filename: str, target_filename: str
    ) -> str:
        """
        Load an HTML report from a source folder and store it in the artifacts directory.

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
        if not self.file_exists(source_path):
            raise FileNotFoundError(f"Source HTML file not found: {source_path}")

        content = self.load_file(source_path)
        if not content:
            raise FileNotFoundError(f"Source HTML file is empty: {source_path}")

        return self.save_html_report(content, target_filename)

    def load_and_store_xml_report(
        self, source_folder: str, source_filename: str, target_filename: str
    ) -> str:
        """
        Load an XML report from a source folder and store it in the company data directory.

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
        if not self.file_exists(source_path):
            raise FileNotFoundError(f"Source XML file not found: {source_path}")

        content = self.load_file(source_path)
        if not content:
            raise FileNotFoundError(f"Source XML file is empty: {source_path}")

        return self.save_xml(content, target_filename)

    def get_risk_data_by_uuid(self, uuid: str) -> dict[str, Any] | None:
        """
        Load and parse risk data XML file based on risk run UUID.

        Args:
            uuid: UUID of the risk data file (without extension)

        Returns:
            Dictionary containing:
            - uuid: UUID of the risk data
            - path: Full path to the XML file
            - data: Parsed XML data as a dictionary
            - risks_report_path: Full path to risk HTML report if it exists, None otherwise

        Raises:
            FileNotFoundError: If no matching XML file is found
            ET.ParseError: If the XML cannot be parsed
            Exception: For any other parsing issues
        """
        try:
            xml_path = os.path.join(str(self.company_data_dir), f"{uuid}_risks.xml")

            if not self.file_exists(xml_path):
                raise FileNotFoundError(f"No risk data XML file found for UUID: {uuid}")

            xml_content = self.load_file(xml_path)
            if not xml_content:
                raise FileNotFoundError(
                    f"Risk data XML file exists but is empty: {xml_path}"
                )

            root = ET.fromstring(xml_content)

            risk_info: dict[str, Any] = {
                "uuid": uuid,
                "path": xml_path,
                "data": self._xml_to_dict(root),
            }

            risks_report_path = os.path.join(
                self.artifacts_dir, f"{uuid}_risks_report.html"
            )
            risk_info["risks_report_path"] = (
                os.path.abspath(risks_report_path)
                if self.file_exists(risks_report_path)
                else None
            )

            return risk_info
        except Exception:
            import traceback

            print(f"Error processing risk data with UUID {uuid}:")
            print(traceback.format_exc())
            return None


# Create a singleton instance to be imported
persistence_service = PersistenceService.get_instance()

if __name__ == "__main__":
    """
    Run this script directly to test the list_cached_companies functionality.
    
    Example usage:
    python persistence_service.py
    """

    # Get the persistence service instance
    service = PersistenceService.get_instance()

    # List all cached companies with their parsed data
    companies = service.list_cached_companies()

    # Print the results
    print(f"Found {len(companies)} company XML files:")
    for i, company in enumerate(companies, 1):
        print(f"\n{i}. Company: {company['name']}")
        print(f"   File: {company['path']}")

        # Print parsed data status
        if company["data"]:
            print("   Data: Successfully parsed")

            # Extract company name if available
            name_data = None
            try:
                name_data = company["data"]["CompanyData"]["CompanyIdentity"]["Name"]
                if (
                    "FinalApprovedName" in name_data
                    and "value" in name_data["FinalApprovedName"]
                ):
                    print(
                        f"   Official Name: {name_data['FinalApprovedName']['value']}"
                    )
            except (KeyError, TypeError):
                pass

            # Print data structure summary
            print("   Data structure:")
            if company["data"].get("CompanyData"):
                for section in company["data"]["CompanyData"]:
                    print(f"      - {section}")
        else:
            print("   Data: Failed to parse XML")

    # If no companies found, suggest creating a test file
    if not companies:
        print("\nNo company XML files found in the company data directory.")
        print(f"Directory: {service.company_data_dir}")
        print("\nYou can create a test XML file with this example command:")
        test_xml_path = os.path.join(str(service.company_data_dir), "test_company.xml")
        print(
            f"echo '<CompanyData><CompanyIdentity><Name><FinalApprovedName>Test Company</FinalApprovedName></Name></CompanyIdentity></CompanyData>' > {test_xml_path}"
        )
