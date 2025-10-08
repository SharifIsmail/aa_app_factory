import hashlib
import os

import requests
from smolagents.models import LiteLLMModel
from smolagents.tools import Tool

from service.lksg_core.agent_extract_company_data.prompts import (
    FINALIZE_CORRECTED_COMPANY_DATA_PROMPT,
    GENERATE_XML_COMPANY_DATA_PROMPT,
    PROCESS_IN_MEMORY_DATA_PROMPT,
    PROVIDE_FEEDBACK_COMPANY_DATA_PROMPT,
)
from service.lksg_core.models import TaskStatus, ToolLog, WorkLog
from service.lksg_core.persistence_service import persistence_service
from service.lksg_core.tools.general_tools import DataStorage, InMemoryStorage


class CompanyDataByDomainTool(Tool):
    name = "company_data_by_domain"
    description = (
        """Retrieves company data using Abstract API based on company website domain"""
    )
    inputs = {
        "domain": {
            "type": "string",
            "description": "The company domain to search for (without www).",
        }
    }
    output_type = "object"

    def __init__(
        self, data_storage: DataStorage, execution_id: str, work_log: WorkLog, **kwargs
    ) -> None:
        super().__init__()
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.api_key = os.getenv("ABSTRACT_API_KEY")
        if not self.api_key:
            raise ValueError("Missing ABSTRACT_API_KEY environment variable")

    def forward(self, domain: str) -> str:
        tool_log = ToolLog(tool_name=self.name, params={"domain": domain})
        self.work_log.tool_logs.append(tool_log)

        if domain.startswith("www."):
            tool_log.result = "Error: Domain should not include 'www.'"
            return "Error: Domain should not include 'www.'"

        # Create a cache key based on domain
        domain_hash = hashlib.md5(domain.encode("utf-8")).hexdigest()
        cache_file = f"cache_abstract_api_{domain_hash}.json"

        # Try to load from cache first
        cached_result = persistence_service.load_from_cache(cache_file)

        if cached_result:
            print(f"CACHE HIT: Abstract API search for '{domain}'")
            result = cached_result
            self.data_storage.store_with_source(result, result.get("source_url", ""))
        else:
            print(f"CACHE MISS: Abstract API search for '{domain}'")
            try:
                response = requests.get(
                    f"https://companyenrichment.abstractapi.com/v2/?api_key={self.api_key}&domain={domain}"
                )

                if response.status_code != 200:
                    error_msg = f"API error: {response.status_code} - {response.text}"
                    tool_log.result = error_msg
                    return error_msg

                result = response.json()
                result["source_url"] = (
                    f"abstractapi.com/companyenrichment?domain={domain}"
                )

                # Cache the result
                persistence_service.save_to_cache(cache_file, result)
                self.data_storage.store_with_source(result, result["source_url"])

            except Exception as e:
                import traceback

                traceback.print_exc()
                tool_log.result = f"Error: {str(e)}"
                return "Error: " + str(e)

        tool_log.result = result
        return result


class ProvideFeedbackCompanyDataTool(Tool):
    name = "provide_feedback_company_data"
    description = "Checks and provides feedback on company data."
    inputs = {
        "company_name": {
            "type": "string",
            "description": "The name of the company to validate.",
        },
        "company_data": {
            "type": "string",
            "description": "The company data to validate. Make sure to convert everything as a single string with all the data points.",
        },
    }
    output_type = "string"

    def __init__(
        self, lite_llm_model: LiteLLMModel, execution_id: str, work_log: WorkLog
    ) -> None:
        self.model = lite_llm_model
        self.execution_id = execution_id
        self.work_log = work_log
        self.is_initialized = True

    def forward(self, company_name: str, company_data: str) -> str:
        tool_log = ToolLog(tool_name=self.name, params={"company": company_name})
        self.work_log.tool_logs.append(tool_log)

        try:
            prompt = PROVIDE_FEEDBACK_COMPANY_DATA_PROMPT.format(
                company_name=company_name, company_data=company_data
            )
            messages = [{"role": "user", "content": [{"text": prompt, "type": "text"}]}]
            response = self.model(messages)
            try:
                result = response.raw.choices[0].message.content
                tool_log.result = result
                return result
            except Exception:
                import traceback

                traceback.print_exc()
                tool_log.result = "NO_DATA_FOUND"
                return "NO_DATA_FOUND"
        except Exception as e:
            import traceback

            traceback.print_exc()
            tool_log.result = f"Error: {str(e)}"
            return "Error: " + str(e)


class ProcessInMemoryCompanyDataTool(Tool):
    name = "process_in_memory_company_data"
    description = "Processes the company data in the in-memory storage."
    inputs = {
        "company_name": {
            "type": "string",
            "description": "The name of the company to validate.",
        },
        "company_data": {
            "type": "string",
            "description": "The company data to validate. Make sure to convert everything as a single string with all the data points.",
        },
        "in_memory_data": {
            "type": "string",
            "description": "The complete log of the data research process",
        },
    }
    output_type = "string"

    def __init__(
        self, lite_llm_model: LiteLLMModel, execution_id: str, work_log: WorkLog
    ) -> None:
        self.model = lite_llm_model
        self.execution_id = execution_id
        self.work_log = work_log
        self.is_initialized = True

    def forward(self, company_name: str, company_data: str, in_memory_data: str) -> str:
        tool_log = ToolLog(tool_name=self.name, params={"company": company_name})
        self.work_log.tool_logs.append(tool_log)

        try:
            prompt = PROCESS_IN_MEMORY_DATA_PROMPT.format(
                company_name=company_name,
                company_data=company_data,
                in_memory_data=in_memory_data,
            )
            messages = [{"role": "user", "content": [{"text": prompt, "type": "text"}]}]
            response = self.model(messages)
            try:
                result = response.raw.choices[0].message.content
                tool_log.result = result
                return result
            except Exception:
                import traceback

                traceback.print_exc()
                tool_log.result = "NO_DATA_FOUND"
                return "NO_DATA_FOUND"
        except Exception as e:
            import traceback

            traceback.print_exc()
            tool_log.result = f"Error: {str(e)}"
            return "Error: " + str(e)


class IntegrateFeedbackCompanyDataTool(Tool):
    name = "integrate_feedback_company_data"
    description = "Integrates feedback on company data."
    inputs = {
        "company_name": {"type": "string", "description": "The name of the company"},
        "original_company_data": {
            "type": "string",
            "description": "The original company data to validate. Make sure to convert everything as a single string with all the data points.",
        },
        "feedback": {
            "type": "string",
            "description": "The feedback on the company data. Make sure to convert everything as a single string.",
        },
        "fixes": {
            "type": "string",
            "description": "The fixes to the company data. Make sure to convert everything as a single string.",
        },
    }
    output_type = "string"

    def __init__(
        self, lite_llm_model: LiteLLMModel, execution_id: str, work_log: WorkLog
    ):
        self.model = lite_llm_model
        self.execution_id = execution_id
        self.work_log = work_log
        self.is_initialized = True

    def forward(
        self, company_name: str, original_company_data: str, feedback: str, fixes: str
    ) -> str:
        tool_log = ToolLog(tool_name=self.name, params={"company": company_name})
        self.work_log.tool_logs.append(tool_log)

        try:
            prompt = FINALIZE_CORRECTED_COMPANY_DATA_PROMPT.format(
                company_name=company_name,
                original_company_data=original_company_data,
                feedback=feedback,
                fixes=fixes,
            )
            messages = [{"role": "user", "content": [{"text": prompt, "type": "text"}]}]

            response = self.model(messages)
            try:
                result = response.raw.choices[0].message.content
                tool_log.result = result
                return result
            except Exception:
                import traceback

                traceback.print_exc()
                tool_log.result = "NO_DATA_FOUND"
                return "NO_DATA_FOUND"
        except Exception as e:
            import traceback

            traceback.print_exc()
            tool_log.result = f"Error: {str(e)}"
            return "Error: " + str(e)


class GenerateStructuredCompanyDataReportTool(Tool):
    name = "generate_structured_company_data_report"
    description = "Takes as input company data and returns a structured report of the company data."
    inputs = {
        "company_data": {"type": "string", "description": "The company data."},
        "company_name": {"type": "string", "description": "The name of the company"},
    }
    output_type = "string"

    def __init__(
        self, lite_llm_model: LiteLLMModel, execution_id: str, work_log: WorkLog
    ):
        self.model = lite_llm_model
        self.execution_id = execution_id
        self.work_log = work_log
        self.is_initialized = True

    def forward(self, company_data: str, company_name: str) -> str:
        tool_log = ToolLog(tool_name=self.name, params={"company": company_name})
        self.work_log.tool_logs.append(tool_log)

        try:
            prompt = GENERATE_XML_COMPANY_DATA_PROMPT.format(
                company_name=company_name, company_data=company_data
            )
            messages = [{"role": "user", "content": [{"text": prompt, "type": "text"}]}]
            response = self.model(messages)
            try:
                result = response.raw.choices[0].message.content
                tool_log.result = result
                return result
            except Exception:
                import traceback

                traceback.print_exc()
                tool_log.result = "NO_DATA_FOUND"
                return "NO_DATA_FOUND"
        except Exception as e:
            import traceback

            traceback.print_exc()
            tool_log.result = f"Error: {str(e)}"
            return "Error: " + str(e)


if __name__ == "__main__":
    import sys

    from service.lksg_core.models import WorkLog
    from service.lksg_core.tools.general_tools import InMemoryStorage

    if len(sys.argv) != 2:
        print("Usage: python company_search_data_tools.py <domain>")
        print("Example: python company_search_data_tools.py airbnb.com")
        sys.exit(1)

    domain = sys.argv[1]
    data_storage = InMemoryStorage()
    work_log = WorkLog(
        id="cli", status=TaskStatus.IN_PROGRESS, tasks=[], company_name=domain
    )

    tool = CompanyDataByDomainTool(
        data_storage=data_storage, execution_id="cli", work_log=work_log
    )

    try:
        result = tool.forward(domain)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
