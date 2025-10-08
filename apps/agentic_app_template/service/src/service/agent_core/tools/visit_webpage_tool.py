import re
import subprocess
import traceback
from urllib.parse import urlparse

import requests
from loguru import logger
from markdownify import markdownify
from smolagents import Tool
from smolagents.utils import truncate_content

from service.agent_core.models import DataStorage, ToolLog, WorkLog


class VisitWebpageUserAgentTool(Tool):
    name = "visit_webpage"
    description = """Visits a webpage at the given url and reads its content as a markdown string.
    IMPORTANT: The url MUST be a valid, complete URL starting with http:// or https:// (e.g., https://example.com).
    This tool will fail if given an invalid URL or a partial URL without a scheme.
    """
    inputs = {
        "url": {
            "type": "string",
            "description": "The complete url of the webpage to visit, including http:// or https:// prefix.",
        }
    }
    output_type = "string"

    def __init__(
        self,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
        repo_key: str,
    ):
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.repo_key = repo_key
        self.is_initialized = True
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }
        self.truncation_length = 100000
        logger.info(
            f"VisitWebpageUserAgentTool initialized with repo_key: {self.repo_key}"
        )

    def _fetch_with_requests(self, url: str) -> str:
        """Fetch webpage content using the requests library"""
        try:
            # Send a GET request to the URL with the specified headers
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # Convert the HTML content to Markdown
            markdown_content = markdownify(response.text).strip()

            # Remove multiple line breaks
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

            return truncate_content(markdown_content, self.truncation_length)
        except Exception as e:
            logger.error(f"Request failed with requests: {e}")
            logger.error(traceback.format_exc())
            raise

    def _fetch_with_curl(self, url: str) -> str:
        """Fetch webpage content using curl as fallback"""
        # Construct the curl command with the same headers
        curl_command = ["curl", url]

        # Add all headers to the curl command
        for key, value in self.headers.items():
            curl_command.extend(["-H", f"{key}: {value}"])

        # Execute the curl command and capture the output
        process = subprocess.Popen(
            curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        # Check for errors
        if process.returncode != 0:
            raise Exception(f"curl failed with error: {stderr.decode()}")

        html_content = stdout.decode()

        # Convert the HTML content to Markdown
        markdown_content = markdownify(html_content).strip()

        # Remove multiple line breaks
        markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

        return truncate_content(markdown_content, self.truncation_length)

    def _process_content(self, content: str, url: str, tool_log: ToolLog) -> str:
        """Process the fetched content, store it, and return the result"""
        try:
            # Store content in the specified repository
            content_key = f"webpage_{hash(url) & 0xFFFFFFFF}"
            data = {"url": url, "content": content, "timestamp": tool_log.timestamp}
            self.data_storage.store_to_repo(self.repo_key, content_key, data)
            logger.info(
                f"Stored webpage content from {url} to repository {self.repo_key} with key {content_key}"
            )

            tool_log.result = content
            return content
        except Exception as e:
            error_msg = f"Error storing webpage content: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            tool_log.result = error_msg
            raise

    def _validate_url(self, url: str) -> bool:
        """Validate if the given URL has a scheme and netloc."""
        # Handle non-string input
        if not isinstance(url, str):
            return False

        # Basic URL validation - must start with http:// or https://
        if not url.startswith(("http://", "https://")):
            return False

        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception as e:
            logger.error(f"URL parsing error: {e}")
            return False

    def forward(self, url: str) -> str:
        # Create a tool log entry
        tool_log = ToolLog(tool_name=self.name, params={"url": url})
        self.work_log.tool_logs.append(tool_log)

        logger.info(f"Visiting webpage: {url}")

        # Handle non-string URL input and validate URL
        if not isinstance(url, str) or not self._validate_url(url):
            error_msg = f"Error: Invalid URL '{url}'. URL must be a valid web address starting with http:// or https://"
            tool_log.result = error_msg
            logger.error(error_msg)
            return error_msg

        # Check for PDF files
        if url.lower().endswith(".pdf"):
            error_msg = "Error: Cannot visit PDF files directly. Please provide a URL to a webpage."
            tool_log.result = error_msg
            logger.error(error_msg)
            return error_msg

        try:
            # Try fetching with requests first
            try:
                logger.info(f"Attempting to fetch {url} using requests")
                content = self._fetch_with_requests(url)
                return self._process_content(content, url, tool_log)
            except Exception as e:
                logger.error(f"Request method failed: {e}. Falling back to curl.")

                # If requests fails, try with curl as fallback
                try:
                    logger.info(f"Attempting to fetch {url} using curl")
                    content = self._fetch_with_curl(url)
                    return self._process_content(content, url, tool_log)
                except Exception as curl_e:
                    error_msg = f"An unexpected error occurred during curl execution: {str(curl_e)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    tool_log.result = error_msg
                    return error_msg

        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            tool_log.result = error_msg
            return error_msg
