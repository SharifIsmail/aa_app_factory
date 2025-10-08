import queue
import re
import subprocess
from abc import ABC, abstractmethod
from typing import Optional

import requests
from colorama import Fore, Style
from markdownify import markdownify
from smolagents.models import LiteLLMModel
from smolagents.tools import Tool

from service.lksg_core.agent_extract_company_data.prompts import (
    GENERATE_XML_COMPANY_DATA_PROMPT,
)
from service.lksg_core.models import ToolLog, WorkLog
from service.lksg_core.prompts import FIX_XML_PROMPT


class DataStorage(ABC):
    @abstractmethod
    def store_with_source(self, data_item: str, source_url: str) -> None:
        pass

    @abstractmethod
    def store(self, data_item: dict) -> None:
        pass

    @abstractmethod
    def retrieve_all(self) -> list:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class InMemoryStorage(DataStorage):
    def __init__(self) -> None:
        self.storage: queue.Queue = queue.Queue()

    def store_with_source(self, data_item: str, source_url: str):
        item = {"data": data_item, "source_url": source_url}
        self.store(item)
        return item

    def store(self, data_item: dict) -> None:
        print(Fore.GREEN + f"Storing data {data_item}" + Style.RESET_ALL)
        self.storage.put(data_item)

    def retrieve_all(self) -> list:
        with self.storage.mutex:
            return list(self.storage.queue)

    def clear(self) -> None:
        with self.storage.mutex:
            self.storage.queue.clear()


class VisitWebpageUserAgentTool(Tool):
    name = "visit_webpage"
    description = "Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages."
    inputs = {
        "url": {
            "type": "string",
            "description": "The url of the webpage to visit.",
        }
    }
    output_type = "string"

    def __init__(
        self, data_storage: DataStorage, execution_id: str, work_log: WorkLog
    ) -> None:
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.is_initialized = True

    def forward(self, url: str) -> str:
        # TODO is url points to a PDF return an error message stating PDF cannot be visited
        tool_log = ToolLog(tool_name=self.name, params={"url": url})
        self.work_log.tool_logs.append(tool_log)

        if url.lower().endswith(".pdf"):
            error_msg = "Error: Cannot visit PDF files directly. Please provide a URL to a webpage."
            tool_log.result = error_msg
            return error_msg
        try:
            from smolagents.utils import truncate_content
        except ImportError as e:
            error_msg = "You must install packages `markdownify` and `requests` to run this tool: for instance run `pip install markdownify requests`."
            tool_log.result = error_msg
            raise ImportError(error_msg) from e
        try:
            # Define headers to match the curl command
            headers = {
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

            # Send a GET request to the URL with the specified headers
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Convert the HTML content to Markdown
            markdown_content = markdownify(response.text).strip()

            # Remove multiple line breaks
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

            result = truncate_content(markdown_content, 10000)
            self.data_storage.store_with_source(result, url)
            tool_log.result = result
            return result

        except requests.exceptions.RequestException as e:
            print(f"Request failed with requests: {e}. Falling back to curl.")
            try:
                # Construct the curl command
                curl_command = [
                    "curl",
                    url,
                    "-H",
                    "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "-H",
                    "accept-language: en-US,en;q=0.9",
                    "-H",
                    "cache-control: max-age=0",
                    "-H",
                    "priority: u=0, i",
                    "-H",
                    'sec-ch-ua: "Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                    "-H",
                    "sec-ch-ua-mobile: ?0",
                    "-H",
                    'sec-ch-ua-platform: "macOS"',
                    "-H",
                    "sec-fetch-dest: document",
                    "-H",
                    "sec-fetch-mode: navigate",
                    "-H",
                    "sec-fetch-site: none",
                    "-H",
                    "sec-fetch-user: ?1",
                    "-H",
                    "upgrade-insecure-requests: 1",
                    "-H",
                    "user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                ]

                # Execute the curl command and capture the output
                process = subprocess.Popen(
                    curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()

                # Check for errors
                if process.returncode != 0:
                    error_msg = f"curl failed with error: {stderr.decode()}"
                    tool_log.result = error_msg
                    return error_msg

                html_content = stdout.decode()

                # Convert the HTML content to Markdown
                markdown_content = markdownify(html_content).strip()

                # Remove multiple line breaks
                markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

                result = truncate_content(markdown_content, 10000)
                tool_log.result = result
                return result

            except Exception as e:
                error_msg = (
                    f"An unexpected error occurred during curl execution: {str(e)}"
                )
                tool_log.result = error_msg
                return error_msg
        except requests.exceptions.Timeout:
            error_msg = (
                "The request timed out. Please try again later or check the URL."
            )
            tool_log.result = error_msg
            return error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            tool_log.result = error_msg
            return error_msg


class GenerateStructuredCompanyDataReportTool(Tool):
    name = "generate_structured_company_data_report"
    description = "Takes as input company data and returns a structured report of the company data."
    inputs = {
        "company_data": {"type": "string", "description": "The company data."},
        "company_name": {"type": "string", "description": "The name of the company"},
    }
    output_type = "string"

    def __init__(self, work_log: Optional[WorkLog] = None):
        self.model_id = "gpt-4o"
        self.custom_role_conversions = {
            "tool-call": "assistant",
            "tool-response": "user",
        }
        self.model = LiteLLMModel(
            self.model_id,
            custom_role_conversions=self.custom_role_conversions,
            max_completion_tokens=8192,
        )
        self.is_initialized = True
        self.work_log = work_log

    def forward(self, company_data: str, company_name: str) -> str:
        tool_log = None
        if self.work_log:
            tool_log = ToolLog(tool_name=self.name, params={"company": company_name})
            self.work_log.tool_logs.append(tool_log)

        try:
            prompt = GENERATE_XML_COMPANY_DATA_PROMPT.format(
                company_name=company_name, company_data=company_data
            )
            messages = [{"role": "user", "content": prompt}]
            response = self.model(messages)
            result = response.content

            if tool_log:
                tool_log.result = result
            return result
        except Exception as e:
            import traceback

            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            if tool_log:
                tool_log.result = error_msg
            return error_msg


class FixXMLTool(Tool):
    name = "fix_xml"
    description = "Takes as input a potentially malformed XML string and returns a corrected XML string."
    inputs = {"xml_string": {"type": "string", "description": "The XML string to fix."}}
    output_type = "string"

    def __init__(
        self, lite_llm_model: LiteLLMModel, work_log: Optional[WorkLog] = None
    ):
        self.model = lite_llm_model
        self.work_log = work_log
        self.is_initialized = True

    def forward(self, xml_string: str) -> str:
        tool_log = None
        if self.work_log:
            tool_log = ToolLog(
                tool_name=self.name,
                params={
                    "xml_string": xml_string[:100] + "..."
                    if len(xml_string) > 100
                    else xml_string
                },
            )
            self.work_log.tool_logs.append(tool_log)

        try:
            prompt = FIX_XML_PROMPT.format(xml_string=xml_string)
            messages = [{"role": "user", "content": [{"text": prompt, "type": "text"}]}]
            response = self.model(messages)
            try:
                result = response.raw.choices[0].message.content
                if tool_log:
                    tool_log.result = result
                return result
            except Exception as e:
                import traceback

                traceback.print_exc()
                error_msg = f"Error: {str(e)}"
                if tool_log:
                    tool_log.result = error_msg
                return error_msg
        except Exception as e:
            import traceback

            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            if tool_log:
                tool_log.result = error_msg
            return error_msg


class InMemoryDataStoreTool(Tool):
    name = "store_data"
    description = "Stores data in a temporary in-memory storage. This tool MUST be invoked whenever new data is discovered during the research process. Each data item must have 'data' and 'source_url'."
    inputs = {
        "data": {"type": "string", "description": "The data to store."},
        "source_url": {"type": "string", "description": "The source URL of the data."},
    }
    output_type = "string"

    def __init__(
        self, storage: Optional[DataStorage] = None, work_log: Optional[WorkLog] = None
    ):
        self.storage = storage if storage is not None else InMemoryStorage()
        self.work_log = work_log
        self.is_initialized = True

    def retrieve_all(self) -> list:
        return self.storage.retrieve_all()

    def forward(self, data: str, source_url: str) -> str:
        tool_log = None
        if self.work_log:
            tool_log = ToolLog(
                tool_name=self.name,
                params={
                    "data": data[:100] + "..." if len(data) > 100 else data,
                    "source_url": source_url,
                },
            )
            self.work_log.tool_logs.append(tool_log)

        try:
            print(
                Fore.GREEN
                + f"Storing data from source '{source_url}'. Data={data}"
                + Style.RESET_ALL
            )
            data_item = {"data": data, "source_url": source_url}
            self.storage.store(data_item)
            result = f"Data stored successfully from {source_url}"

            if tool_log:
                tool_log.result = result
            return result
        except Exception as e:
            import traceback

            traceback.print_exc()
            error_msg = f"Error storing data: {str(e)}"
            if tool_log:
                tool_log.result = error_msg
            return error_msg
