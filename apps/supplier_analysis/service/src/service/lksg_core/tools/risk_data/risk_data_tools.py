import json
import re
import threading
from typing import Any, Dict, List, Optional

from smolagents import Tool
from smolagents.models import LiteLLMModel

from service.lksg_core.agent_extract_company_risks.prompts import (
    EXTRACT_LKSG_INCIDENTS_PROMPT,
)
from service.lksg_core.models import ToolLog, WorkLog
from service.lksg_core.tools.general_tools import DataStorage
from service.lksg_core.tools.risk_data.google_search_with_source_url_tool import (
    GoogleSearchWithSourceURLTool,
)


class LogIncidentsToQueueTool(Tool):
    name = "log_incidents_to_queue"
    description = """Log one or multiple discovered incidents to the events processing queue for further investigation"""
    inputs = {
        "incident_descriptions": {
            "type": "array",
            "description": "Incident descriptions to log",
        }
    }
    output_type = "string"

    def __init__(
        self,
        incident_queue: List[str],
        work_log: WorkLog = None,
        model: LiteLLMModel = None,
    ):
        super().__init__()
        if model is None:
            raise ValueError("Model must be provided to LogIncidentsToQueueTool")
        self.incident_queue = incident_queue
        self.queue_lock = threading.Lock()
        self.work_log = work_log
        self.model = model

    def _process_search_results(
        self, search_results: List[Dict[str, Any]]
    ) -> List[str]:
        if not search_results:
            return []

        # Convert search results to a string format for the LLM
        search_results_str = json.dumps(search_results, indent=2)

        # Get the prompt and format it with the search results
        prompt = EXTRACT_LKSG_INCIDENTS_PROMPT.format(search_results=search_results_str)
        messages = [{"role": "user", "content": [{"text": prompt, "type": "text"}]}]

        try:
            # Call the LLM to process the results
            response = self.model(messages)
            result = response.raw.choices[0].message.content

            if result == "No relevant incidents found.":
                return []

            # Split the response into individual incidents
            incidents = result.split("----- EVENT -----")[
                1:
            ]  # Skip the first empty split
            formatted_incidents = []
            for incident in incidents:
                if incident.strip():
                    formatted_incidents.append(incident.strip())

            return formatted_incidents
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error processing search results with LLM: {str(e)}")
            return []

    def forward(self, incident_descriptions: List[str]) -> str:
        tool_log = None
        if self.work_log:
            tool_log = ToolLog(
                tool_name=self.name,
                params={"incident_descriptions": str(incident_descriptions)},
            )
            self.work_log.tool_logs.append(tool_log)

        # Ensure we have a list
        if not isinstance(incident_descriptions, list):
            incident_descriptions = [incident_descriptions]

        # Process the search results through the LLM
        # Convert string descriptions to dictionaries if needed
        search_results_dicts = []
        for item in incident_descriptions:
            if isinstance(item, str):
                try:
                    # Try to parse JSON strings
                    parsed = json.loads(item)
                    search_results_dicts.append(parsed)
                except json.JSONDecodeError:
                    # If not JSON, create a simple dict
                    search_results_dicts.append({"text": item})
            else:
                search_results_dicts.append(item)

        processed_incidents = self._process_search_results(search_results_dicts)

        with self.queue_lock:
            incidents_added = 0
            for description in processed_incidents:
                if description.strip():
                    self.incident_queue.append(description)
                    incidents_added += 1

                if self.work_log and hasattr(self.work_log, "extracted_data"):
                    source_key = f"INCIDENT_{len(self.work_log.extracted_data)}"
                    desc = re.sub(r"----- EVENT #\d+ -----\s*", "", description)
                    self.work_log.extracted_data[source_key] = desc

            queue_length = len(self.incident_queue)

        if incidents_added == 0:
            result = f"No valid incidents were found in the search results. Queue remains at {queue_length} incidents."
        elif incidents_added == 1:
            result = f"1 incident logged successfully. Queue now contains {queue_length} incidents."
        else:
            result = f"{incidents_added} incidents logged successfully. Queue now contains {queue_length} incidents."

            print("\n\n\n\n\n\n")
            print("-------")
            if self.work_log and hasattr(self.work_log, "extracted_data"):
                print(self.work_log.extracted_data)
            print("-------")
            print("\n\n\n\n\n\n")

        if tool_log:
            tool_log.result = result

        return result

    def update_queue(self, incidents: List[str]) -> None:
        """
        Safely update the queue with multiple incidents while respecting the lock.

        Args:
            incidents: List of incident descriptions to add to the queue
        """
        with self.queue_lock:
            for incident in incidents:
                if incident.strip():
                    self.incident_queue.append(incident)
                    if self.work_log and hasattr(self.work_log, "extracted_data"):
                        source_key = f"INCIDENT_{len(self.work_log.extracted_data)}"
                        description = re.sub(r"----- EVENT #\d+ -----\s*", "", incident)
                        self.work_log.extracted_data[source_key] = description


class SearchAndLogIncidentsTool(Tool):
    name = "search_and_log_incidents"
    description = (
        """Performs a google web search for incidents and logs them to the queue"""
    )
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."},
        "filter_year": {
            "type": "integer",
            "description": "Optionally restrict results to a certain year",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(
        self,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
        incident_queue: List[str],
        model: LiteLLMModel,
        provider: str = "serpapi",
    ):
        super().__init__()
        self.search_tool = GoogleSearchWithSourceURLTool(
            data_storage=data_storage,
            execution_id=execution_id,
            work_log=work_log,
            provider=provider,
        )
        self.log_tool = LogIncidentsToQueueTool(
            incident_queue=incident_queue, work_log=work_log, model=model
        )
        self.work_log = work_log

    def forward(self, query: str, filter_year: Optional[int] = None) -> str:
        tool_log = ToolLog(
            tool_name=self.name,
            params={
                "query": query,
                "filter_year": str(filter_year) if filter_year is not None else "",
            },
        )
        self.work_log.tool_logs.append(tool_log)

        try:
            # First perform the search
            search_result = self.search_tool.forward(query, filter_year)

            # Extract the search results from the formatted string
            search_results = []
            for line in search_result.split("\n"):
                if line.startswith("{"):
                    try:
                        result = json.loads(line)
                        search_results.append(result)
                    except json.JSONDecodeError:
                        continue

            # Log the incidents from the search results
            log_result = self.log_tool.forward(search_results)

            # Combine the results
            result = (
                f"Search Results:\n{search_result}\n\nLogging Results:\n{log_result}"
            )
            tool_log.result = result
            return result

        except Exception as e:
            import traceback

            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            tool_log.result = error_msg
            return error_msg
