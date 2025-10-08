# Standard library imports
from typing import Optional, Union

# Third-party imports
import requests
from bs4 import BeautifulSoup, PageElement
from loguru import logger
from markdownify import markdownify
from smolagents import Tool

# Local imports
from service.law_core.models import ToolLog, WorkLog
from service.law_core.utils.text_utils import (
    clean_text,
    remove_images_from_text,
    remove_xml_metadata_from_html_content,
)
from service.storage.data_storage import DataStorage


class FetchWebpageDivContentTool(Tool):
    name = "fetch_webpage_div_content"
    description = (
        "Fetches a webpage at the given URL and extracts its content using BeautifulSoup. "
        "Can optionally extract content from a specific div by ID or class name."
    )
    inputs = {
        "url": {
            "type": "string",
            "description": "The URL of the webpage to fetch.",
        },
        "div_id": {
            "type": "string",
            "description": "Optional ID of an element to extract. If provided, only content from this element will be returned.",
            "required": False,
            "nullable": True,
        },
        "class_name": {
            "type": "string",
            "description": "Optional class name to extract. If provided, only content from the first element with this class will be returned.",
            "required": False,
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(
        self,
        execution_id: str,
        work_log: WorkLog,
        repo_key: Optional[str],
        data_storage: DataStorage = None,
    ) -> None:
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.repo_key = repo_key
        self.is_initialized = True

    def check_element_exists(
        self, url: str, div_id: str = None, class_name: str = None
    ) -> bool:
        """
        Checks if an element with the given ID or class exists on the page.

        Args:
            url: The URL of the page to check
            div_id: The ID of the element to look for
            class_name: The class name to look for

        Returns:
            bool: True if the element exists, False otherwise
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            if div_id:
                target_element = soup.find(id=div_id)
                exists = target_element is not None
                logger.info(
                    f"Element with ID '{div_id}' check on {url}: {'FOUND' if exists else 'NOT FOUND'}"
                )
                return exists
            elif class_name:
                target_element = soup.find(class_=class_name)
                exists = target_element is not None
                logger.info(
                    f"Element with class '{class_name}' check on {url}: {'FOUND' if exists else 'NOT FOUND'}"
                )
                return exists
            else:
                logger.warning("No ID or class name provided for check")
                return False
        except Exception as e:
            logger.error(f"Error checking element existence: {str(e)}")
            return False

    def forward(
        self, url: str, div_id: str = None, class_name: str = None
    ) -> tuple[bool, str]:
        tool_log = ToolLog(
            tool_name=self.name,
            params={"url": url, "div_id": div_id, "class_name": class_name},
        )
        self.work_log.tool_logs.append(tool_log)

        if url.lower().endswith(".pdf"):
            error_msg = "PDF files cannot be processed directly. Please provide a URL to a webpage instead of a PDF file."
            tool_log.result = error_msg
            return False, error_msg

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            content: Union[BeautifulSoup, PageElement]
            if div_id:
                target_element = soup.find(id=div_id)
                if not target_element:
                    warning_msg = f"Warning: No element with ID '{div_id}' found. Returning full page content instead."
                    logger.warning(warning_msg)
                    content = soup
                else:
                    logger.info(
                        f"Successfully found and extracted element with ID: {div_id}"
                    )
                    content = target_element
            elif class_name:
                target_element = soup.find(class_=class_name)
                if not target_element:
                    error_msg = "The required content could not be found on the page. This might be because the URL is incorrect or the page structure has changed. Please check the URL and try again. If you're not sure which URL to use, visit https://eur-lex.europa.eu/search.html?name=collection%3Aeu-law-legislation&type=named&qid=1745521085009 and choose one of the URLs from that page."
                    logger.error(error_msg)
                    tool_log.result = error_msg
                    return False, error_msg
                else:
                    logger.info(
                        f"Successfully found and extracted element with class: {class_name}"
                    )
                    content = target_element
            else:
                logger.info(
                    "No ID or class name specified. Returning full page content."
                )
                content = soup

            # Remove XML metadata from HTML content before converting to markdown
            content_str = str(content)
            cleaned_content_str = remove_xml_metadata_from_html_content(content_str)
            cleaned_content_str = remove_images_from_text(cleaned_content_str)
            markdown_content = markdownify(cleaned_content_str).strip()
            result = clean_text(markdown_content)
            if self.data_storage and self.repo_key:
                # Create a structured data object to store
                content_key = f"webpage_{hash(url) & 0xFFFFFFFF}"
                data = {
                    "url": url,
                    "content": result,
                    "timestamp": tool_log.timestamp,
                    "div_id": div_id,
                    "class_name": class_name,
                }
                self.data_storage.store_to_repo(self.repo_key, content_key, data)
            tool_log.result = result
            return True, result

        except requests.exceptions.Timeout:
            error_msg = "The request timed out. The server might be busy or the URL might be incorrect. Please try again later or check the URL."
            tool_log.result = error_msg
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"The request failed: {str(e)}. Please check the URL and try again. If you're not sure which URL to use, visit https://eur-lex.europa.eu/search.html?name=collection%3Aeu-law-legislation&type=named&qid=1745521085009 and choose one of the URLs from that page."
            tool_log.result = error_msg
            return False, error_msg
        except Exception as e:
            error_msg = (
                f"An unexpected error occurred: {str(e)}. Please try again later."
            )
            tool_log.result = error_msg
            return False, error_msg
