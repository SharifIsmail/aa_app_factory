import json
import traceback
from enum import Enum
from typing import Any, List

import litellm
from dotenv import load_dotenv
from smolagents import CodeAgent
from smolagents.models import LiteLLMModel

from service.dependencies import with_settings
from service.lksg_core.agent_extract_company_risks.prompts import (
    EVENT_SCOUT_PROMPT,
    EVENT_SCOUT_RISKS_TRY_ONCE_MORE_EXTRA_INSTRUCTIONS,
)
from service.lksg_core.artifacts.generators.risk_data_generator import (
    generate_risk_data_artifact,
)
from service.lksg_core.llm.aleph_alpha_llm_provider import AALLMProvider
from service.lksg_core.models import FlowTask, TaskStatus, WorkLog
from service.lksg_core.persistence_service import persistence_service
from service.lksg_core.tools.general_tools import (
    InMemoryStorage,
    VisitWebpageUserAgentTool,
)
from service.lksg_core.tools.risk_data.risk_data_tools import SearchAndLogIncidentsTool


class TaskKeys(Enum):
    INITIAL_RISK_RESEARCH = "initial_risk_research"
    RISK_ITERATION = "risk_iteration"
    GENERATE_RISK_REPORT = "generate_risk_report"


def initialize_tools(
    lite_llm_model: LiteLLMModel,
    execution_id: str,
    work_log: WorkLog,
    incident_queue: list,
) -> dict:
    in_memory_storage = InMemoryStorage()

    search_and_log_tool = SearchAndLogIncidentsTool(
        data_storage=in_memory_storage,
        execution_id=execution_id,
        work_log=work_log,
        incident_queue=incident_queue,
        model=lite_llm_model,
        provider="serper",
    )
    visit_webpage_tool = VisitWebpageUserAgentTool(
        data_storage=in_memory_storage, execution_id=execution_id, work_log=work_log
    )

    return {
        "in_memory_storage_repo": in_memory_storage,
        "search_and_log_tool": search_and_log_tool,
        "visit_webpage_tool": visit_webpage_tool,
        "log_tool": search_and_log_tool.log_tool,  # Expose the inner log tool
    }


def initialize_model() -> LiteLLMModel:
    settings = with_settings()
    model_id = f"aleph-alpha/{settings.completion_model_name}"
    aa_llm_provider = AALLMProvider()
    litellm.custom_provider_map = [
        {"provider": "aleph-alpha", "custom_handler": aa_llm_provider}
    ]

    custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

    model = LiteLLMModel(
        model_id,
        custom_role_conversions=custom_role_conversions,
        max_completion_tokens=8192,
    )

    return model


def initialize_agents(model: Any, tools: dict) -> dict:
    event_scout_risks_agent = CodeAgent(
        model=model,
        tools=[
            tools["search_and_log_tool"],
            tools["visit_webpage_tool"],
        ],
        additional_authorized_imports=["json"],
        max_steps=10,
        verbosity_level=2,
        planning_interval=None,
        name="google_search_risks_agent",
        provide_run_summary=False,
    )

    return {"event_scout_risks_agent": event_scout_risks_agent}


def create_work_log(
    research_type: str, work_log_id: str, num_iterations: int = 5
) -> WorkLog:
    initial_research_task = FlowTask(
        key=TaskKeys.INITIAL_RISK_RESEARCH.value,
        description="Initiating company risk research",
        status=TaskStatus.PENDING,
    )

    iteration_subtasks = []
    for i in range(1, num_iterations + 1):
        iteration_task = FlowTask(
            key=f"{TaskKeys.RISK_ITERATION.value}_{i}",
            description=f"Risk research iteration {i} of {num_iterations}",
            status=TaskStatus.PENDING,
        )
        iteration_subtasks.append(iteration_task)

    generate_report_task = FlowTask(
        key=TaskKeys.GENERATE_RISK_REPORT.value,
        description="Generating risk assessment report",
        status=TaskStatus.PENDING,
    )

    work_log = WorkLog(
        id=work_log_id,
        status=TaskStatus.PENDING,
        tasks=[initial_research_task] + iteration_subtasks + [generate_report_task],
    )

    # Store the research type in the work log
    work_log.research_type = research_type

    return work_log


def extract_company_risks(
    company_data: dict, execution_id: str, work_log: WorkLog, num_iterations: int = 5
):
    load_dotenv()

    # Determine number of iterations based on research type
    research_type = (
        work_log.research_type
        if hasattr(work_log, "research_type")
        else "comprehensive"
    )
    num_iterations = 5 if research_type == "comprehensive" else 1

    # Store the company name directly in the work log
    work_log.company_name = company_data["company_name"]

    trimmed_company_data = {
        "company_name": company_data["company_name"],
        "company_registration_number": company_data["CompanyIdentity"][
            "RegistrationDetails"
        ]["FinalRegistrationNumber"]["value"],
        "company_industry": company_data["Industry"]["FinalIndustryClassification"][
            "value"
        ],
        "company_products_services": company_data["Industry"]["MainProductsOrServices"][
            "value"
        ],
        "company_owner": company_data["OwnershipDetails"]["ParentCompany"]["value"],
        "company_directors": str(
            company_data["OwnershipDetails"]["KeyDirectors"]
        ).split(", ")
        if company_data["OwnershipDetails"]["KeyDirectors"]
        else [],
        "company_location": company_data["Headquarters"]["Address"]["value"],
    }

    incident_queue: List[str] = []

    work_log.get_single_task_with_key(
        TaskKeys.INITIAL_RISK_RESEARCH.value
    ).status = TaskStatus.IN_PROGRESS

    model = initialize_model()
    tools = initialize_tools(model, execution_id, work_log, incident_queue)

    work_log.get_single_task_with_key(
        TaskKeys.INITIAL_RISK_RESEARCH.value
    ).status = TaskStatus.COMPLETED

    for iteration in range(1, num_iterations + 1):
        iteration_task_key = f"{TaskKeys.RISK_ITERATION.value}_{iteration}"
        work_log.get_single_task_with_key(
            iteration_task_key
        ).status = TaskStatus.IN_PROGRESS

        cache_file_risks_iteration = (
            f"cache_{company_data['company_name']}_risks_iteration_{iteration}.json"
        )
        cached_queue = persistence_service.load_from_cache(cache_file_risks_iteration)

        if cached_queue:
            incident_queue = json.loads(cached_queue)
            print(
                f"Loaded incident queue from {cache_file_risks_iteration} with {len(incident_queue)} incidents."
            )
            # Update the tool's queue using the proper method
            tools["log_tool"].update_queue(incident_queue)
            work_log.get_single_task_with_key(
                iteration_task_key
            ).status = TaskStatus.COMPLETED
            continue

        print(
            f"\n{'=' * 50}\nStarting iteration {iteration} of {num_iterations}\n{'=' * 50}\n"
        )
        base_prompt = EVENT_SCOUT_PROMPT.format(company_data=trimmed_company_data)
        prompt = base_prompt

        if len(incident_queue) > 0:
            queue_summary = json.dumps(incident_queue, indent=2)
            prompt += EVENT_SCOUT_RISKS_TRY_ONCE_MORE_EXTRA_INSTRUCTIONS.format(
                old_incident_queue=queue_summary
            )

        print(f"Current incident queue size: {len(incident_queue)}")

        try:
            persistence_service.save_to_cache(
                cache_file_risks_iteration, json.dumps(incident_queue, indent=2)
            )
        except Exception as e:
            traceback.print_exc()
            print(f"Error during risk research iteration {iteration}: {str(e)}")

        work_log.get_single_task_with_key(
            iteration_task_key
        ).status = TaskStatus.COMPLETED
        print(
            f"\nIteration {iteration} complete. Incident queue now contains {len(incident_queue)} incidents."
        )

    work_log.get_single_task_with_key(
        TaskKeys.GENERATE_RISK_REPORT.value
    ).status = TaskStatus.IN_PROGRESS

    # Generate and save the final risk report
    final_risk_report = {
        "company_name": company_data["company_name"],
        "company_details": company_data,
        "risk_incidents": incident_queue,
        "total_incidents_found": len(incident_queue),
    }

    # Store the final risk data in the work log
    work_log.extracted_data = final_risk_report

    # Convert the dictionary to a string when passing to generate_risk_data_artifact
    report_path = generate_risk_data_artifact(
        json.loads(json.dumps(final_risk_report)), work_log.id
    )
    work_log.report_file_path = report_path

    work_log.get_single_task_with_key(
        TaskKeys.GENERATE_RISK_REPORT.value
    ).status = TaskStatus.COMPLETED
    work_log.status = TaskStatus.COMPLETED

    return final_risk_report


if __name__ == "__main__":
    company_data = {
        "company_name": "The Shell Petroleum Development Company of Nigeria Limited",
        "company_registration_number": "RC-892",
        "company_industry": "Oil & Gas",
        "company_products_services": "Oil production and natural gas distribution",
        "company_owner": "Royal Dutch Shell Plc",
        "company_directors": ["Osagie Okunbor", "Ronald Adams", "Ralph Gbobo"],
        "company_location": "Nigeria",
    }

    work_log = create_work_log("standard", "test_extraction_id")
    result = extract_company_risks(company_data, "test_execution_id", work_log)
    print(f"Completed extraction with {len(result['risk_incidents'])} incidents found.")
