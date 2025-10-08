import hashlib
import uuid
from enum import Enum
from typing import Any

import litellm
from dotenv import load_dotenv
from smolagents import CodeAgent
from smolagents.agents import ToolCallingAgent
from smolagents.models import LiteLLMModel

from service.dependencies import with_settings
from service.lksg_core.agent_extract_company_data.log_agent_parsers import (
    parse_company_data_from_agent_steps_logs,
    parse_company_data_re_fetch_after_feedback_results,
)
from service.lksg_core.agent_extract_company_data.prompts import (
    ADDRESS_FEEDBACK_PROMPT,
    EXTRACT_COMPANY_DATA_PROMPT,
)
from service.lksg_core.artifacts.generators.company_data_generator import (
    generate_company_data_artifact,
)
from service.lksg_core.llm.aleph_alpha_llm_provider import AALLMProvider
from service.lksg_core.models import FlowTask, TaskStatus, WorkLog
from service.lksg_core.persistence_service import persistence_service
from service.lksg_core.tools.company_data.company_search_data_tools import (
    CompanyDataByDomainTool,
    GenerateStructuredCompanyDataReportTool,
    IntegrateFeedbackCompanyDataTool,
    ProcessInMemoryCompanyDataTool,
    ProvideFeedbackCompanyDataTool,
)
from service.lksg_core.tools.general_tools import (
    InMemoryStorage,
    VisitWebpageUserAgentTool,
)
from service.lksg_core.tools.risk_data.google_search_with_source_url_tool import (
    GoogleSearchWithSourceURLTool,
)
from service.lksg_core.utils import process_and_fix_xml


class TaskKeys(Enum):
    INITIAL_COMPANY_DATA_RESEARCH = "initial_company_data_research"
    EXTRACT_DATA_FROM_RESEARCH_LOGS = "extract_data_from_research_logs"
    COMPUTE_FEEDBACK = "compute_feedback_on_initial_company_data_research"
    FEEDBACK_ITEM = "feedback_item"
    ADDRESS_FEEDBACK = "address_all_feedback_items"
    GENERATE_REPORT = "generate_structured_report"


def initialize_tools(
    lite_llm_model: LiteLLMModel, execution_id: str, work_log: WorkLog
) -> dict[str, Any]:
    in_memory_storage = InMemoryStorage()

    google_search_tool = GoogleSearchWithSourceURLTool(
        provider="serper",
        data_storage=in_memory_storage,
        execution_id=execution_id,
        work_log=work_log,
    )
    # nigeria_search_tool = NigeriaSearchTool(data_storage=in_memory_storage, execution_id=execution_id, work_log=work_log)
    company_data_by_domain_tool = CompanyDataByDomainTool(
        data_storage=in_memory_storage, execution_id=execution_id, work_log=work_log
    )
    visit_webpage_tool = VisitWebpageUserAgentTool(
        data_storage=in_memory_storage, execution_id=execution_id, work_log=work_log
    )
    provide_feedback_company_data_tool = ProvideFeedbackCompanyDataTool(
        lite_llm_model, execution_id=execution_id, work_log=work_log
    )
    integrate_feedback_company_data_tool = IntegrateFeedbackCompanyDataTool(
        lite_llm_model, execution_id=execution_id, work_log=work_log
    )
    generate_structured_company_data_report_tool = (
        GenerateStructuredCompanyDataReportTool(
            lite_llm_model, execution_id=execution_id, work_log=work_log
        )
    )

    process_in_memory_company_data_tool = ProcessInMemoryCompanyDataTool(
        lite_llm_model, execution_id=execution_id, work_log=work_log
    )

    return {
        "in_memory_storage_repo": in_memory_storage,
        "google_search_tool": google_search_tool,
        # "nigeria_search_tool": nigeria_search_tool,
        "company_data_by_domain_tool": company_data_by_domain_tool,
        "visit_webpage_tool": visit_webpage_tool,
        "provide_feedback_company_data_tool": provide_feedback_company_data_tool,
        "integrate_feedback_company_data_tool": integrate_feedback_company_data_tool,
        "generate_structured_company_data_report_tool": generate_structured_company_data_report_tool,
        "process_in_memory_company_data_tool": process_in_memory_company_data_tool,
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


def on_step_complete(memory_step: Any, work_log: WorkLog) -> None:
    """
    Callback method to track search agent steps and progress.
    This follows the signature expected by MultiStepAgent step_callbacks.

    Args:
        memory_step: The ActionStep object containing step information
        work_log: WorkLog instance to store extracted data
    """
    output_content = getattr(memory_step.model_output_message, "content", None)
    data_so_far = parse_company_data_from_agent_steps_logs(output_content)  # type: ignore
    work_log.extracted_data = data_so_far


def initialize_agents(model: Any, tools: dict, work_log: WorkLog) -> dict:
    def step_callback_with_work_log(memory_step):
        return on_step_complete(memory_step, work_log=work_log)

    search_agent = CodeAgent(
        model=model,
        tools=[
            tools["google_search_tool"],
            tools["company_data_by_domain_tool"],
            tools["visit_webpage_tool"],
        ],
        # tools=[tools["google_search_tool"], tools["visit_webpage_tool"]],
        additional_authorized_imports=["json"],
        max_steps=10,
        verbosity_level=2,
        planning_interval=None,
        name="search_agent",
        provide_run_summary=False,
        step_callbacks=[step_callback_with_work_log],
    )

    re_fetch_data_after_feedback_agent = CodeAgent(
        model=model,
        tools=[
            tools["google_search_tool"],
            tools["company_data_by_domain_tool"],
            tools["visit_webpage_tool"],
        ],
        additional_authorized_imports=["json"],
        max_steps=10,
        verbosity_level=2,
        planning_interval=None,
        name="re_fetch_data_after_feedback_agent",
        provide_run_summary=False,
    )

    integrate_feedback_agent = ToolCallingAgent(
        model=model,
        tools=[tools["integrate_feedback_company_data_tool"]],
        max_steps=50,
        verbosity_level=2,
        planning_interval=None,
        name="integrate_feedback_agent",
        step_callbacks=[step_callback_with_work_log],  # Use the same closure
    )

    return {
        "search_agent": search_agent,
        "integrate_feedback_agent": integrate_feedback_agent,
        "re_fetch_data_after_feedback_agent": re_fetch_data_after_feedback_agent,
    }


def fetch_original_company_data(search_agent: Any, company_name: str) -> Any:
    cache_file_original_data = f"cache_{company_name}_original_data.json"
    original_company_data = persistence_service.load_from_cache(
        cache_file_original_data
    )

    # original_company_data = None

    if not original_company_data:
        print("Running search_agent to get original company data...")
        original_company_data = search_agent.run(
            EXTRACT_COMPANY_DATA_PROMPT.format(company_name=company_name)
        )
        persistence_service.save_to_cache(
            cache_file_original_data, original_company_data
        )
    else:
        print("Loading original company data from cache...")

    return original_company_data


def process_in_memory_data(
    process_in_memory_tool: Any,
    company_name: str,
    original_company_data: Any,
    full_research_logs: str,
) -> Any:
    cache_file_in_memory_data = f"cache_{company_name}_in_memory_data.json"
    company_data_fetched_from_research_logs = persistence_service.load_from_cache(
        cache_file_in_memory_data
    )

    # company_data_fetched_from_research_logs = None

    if not company_data_fetched_from_research_logs:
        print(
            "Running process_in_memory_company_data_tool to process in-memory data..."
        )
        company_data_fetched_from_research_logs = process_in_memory_tool.forward(
            company_name=company_name,
            company_data=original_company_data,
            in_memory_data=full_research_logs,
        )
        persistence_service.save_to_cache(
            cache_file_in_memory_data, company_data_fetched_from_research_logs
        )
    else:
        print("Loaded in-memory data processed from cache.")

    return company_data_fetched_from_research_logs


def compute_feedback(
    provide_feedback_tool: Any, company_name: str, original_company_data: Any
) -> Any:
    cache_file_feedback = f"cache_{company_name}_feedback.json"
    feedback = persistence_service.load_from_cache(cache_file_feedback)

    # feedback = None

    if not feedback:
        print("Running provide_feedback_agent to get feedback...")
        feedback = provide_feedback_tool.forward(
            company_name=company_name, company_data=original_company_data
        )
        persistence_service.save_to_cache(cache_file_feedback, feedback)
    else:
        print("Loaded feedback from cache.")

    parts = feedback.split("====TASKS====")
    if len(parts) > 1:
        tasks_str = parts[1]
        feedback_items = [
            item.strip() for item in tasks_str.split("---") if item.strip()
        ]
    else:
        feedback_items = []

    print("\n\n\nFeedback items:", feedback_items, "\n\n\n")

    return feedback_items


def re_fetch_data_after_feedback(
    search_agent: Any, company_name: str, feedback: str, original_company_data: Any
) -> str:
    feedback_hash = hashlib.md5(feedback.encode("utf-8")).hexdigest()
    cache_file_fixed_after_feedback = (
        f"cache_{company_name}_fixed_after_feedback_{feedback_hash}.json"
    )
    fixed_after_feedback = persistence_service.load_from_cache(
        cache_file_fixed_after_feedback
    )

    # fixed_after_feedback = None

    if not fixed_after_feedback:
        print("Running search_agent to fix data after feedback...")
        prompt = ADDRESS_FEEDBACK_PROMPT.format(
            company_name=company_name,
            feedback=feedback,
            original_company_data=original_company_data,
        )
        fixed_after_feedback = search_agent.run(prompt)
        persistence_service.save_to_cache(
            cache_file_fixed_after_feedback, fixed_after_feedback
        )
    else:
        print("Loaded fixed data after feedback from cache.")

    return fixed_after_feedback


def integrate_feedback(
    integrate_feedback_tool: Any,
    company_name: str,
    original_company_data: Any,
    feedback: str,
    fixed_after_feedback: str,
    work_log: WorkLog,
) -> Any:
    combined_string = (
        f"{company_name}{original_company_data}{feedback}{fixed_after_feedback}"
    )
    feedback_hash = hashlib.md5(combined_string.encode("utf-8")).hexdigest()
    cache_file_fixed_company_data = (
        f"cache_{company_name}_fixed_company_data_{feedback_hash}.json"
    )
    fixed_company_data = persistence_service.load_from_cache(
        cache_file_fixed_company_data
    )

    # fixed_company_data = None

    if not fixed_company_data:
        print("Running integrate_feedback_company_data_tool to integrate feedback...")
        fixed_company_data = integrate_feedback_tool.forward(
            company_name=company_name,
            original_company_data=original_company_data,
            feedback=feedback,
            fixes=fixed_after_feedback,
        )
        persistence_service.save_to_cache(
            cache_file_fixed_company_data, fixed_company_data
        )
    else:
        print("Loaded integrated feedback company data from cache.")

    # Parse the structured company data into a flat structure
    structured_data = parse_company_data_re_fetch_after_feedback_results(
        fixed_company_data
    )

    work_log.extracted_data = structured_data

    return fixed_company_data


def generate_structured_report(
    generate_structured_tool: Any,
    model: Any,
    company_name: str,
    fixed_company_data: Any,
    work_log: WorkLog,
) -> str:
    cache_file_structured_company_data = (
        f"cache_{company_name}_structured_company_data.json"
    )
    structured_company_data = persistence_service.load_from_cache(
        cache_file_structured_company_data
    )

    if not structured_company_data:
        print(
            "Running generate_structured_company_data_report_tool to generate structured report..."
        )
        structured_company_data = generate_structured_tool.forward(
            company_data=fixed_company_data, company_name=company_name
        )
        persistence_service.save_to_cache(
            cache_file_structured_company_data, structured_company_data
        )

    structured_company_data_xml = process_and_fix_xml(
        structured_company_data, model, cache_file_structured_company_data
    )

    file_path = persistence_service.save_xml(
        structured_company_data_xml, work_log.id + "_data"
    )

    print(f"Saved XML data to: {file_path}")

    return structured_company_data_xml


def create_work_log(research_type: str = "comprehensive", work_log_id: str = None):
    # Generate a UUID if none provided
    if work_log_id is None:
        work_log_id = str(uuid.uuid4())

    initial_research_task = FlowTask(
        key=TaskKeys.INITIAL_COMPANY_DATA_RESEARCH.value,
        description="Fetching company data from multiple trusted sources",
        status=TaskStatus.PENDING,
    )
    extract_data_from_research_logs_task = FlowTask(
        key=TaskKeys.EXTRACT_DATA_FROM_RESEARCH_LOGS.value,
        description="Distilling key information from collected data sources",
        status=TaskStatus.PENDING,
    )

    if research_type == "comprehensive":
        compute_feedback_task = FlowTask(
            key=TaskKeys.COMPUTE_FEEDBACK.value,
            description="Identifying gaps and inconsistencies in the company profile",
            status=TaskStatus.PENDING,
        )
        feedback_item_task = FlowTask(
            key=TaskKeys.FEEDBACK_ITEM.value + "_1",
            description="no gaps yet",
            status=TaskStatus.PENDING,
        )
        address_feedback_task = FlowTask(
            key=TaskKeys.ADDRESS_FEEDBACK.value,
            description="Filling gaps and resolving inconsistencies in the company data",
            status=TaskStatus.PENDING,
            subtasks=[feedback_item_task],
        )

    generate_report_task = FlowTask(
        key=TaskKeys.GENERATE_REPORT.value,
        description="Creating a detailed company profile with verified information",
        status=TaskStatus.PENDING,
        subtasks=[],
    )

    if research_type == "comprehensive":
        work_log = WorkLog(
            id=work_log_id,
            status=TaskStatus.PENDING,
            tasks=[
                initial_research_task,
                extract_data_from_research_logs_task,
                compute_feedback_task,
                address_feedback_task,
                generate_report_task,
            ],
        )
    else:
        work_log = WorkLog(
            id=work_log_id,
            status=TaskStatus.PENDING,
            tasks=[
                initial_research_task,
                extract_data_from_research_logs_task,
                generate_report_task,
            ],
        )
    return work_log


def extract_company_data(
    company_name: str, execution_id: str, work_log: WorkLog, research_type: str
):
    load_dotenv()

    # Store the company name directly in the work log
    work_log.company_name = company_name

    work_log.get_single_task_with_key(
        TaskKeys.INITIAL_COMPANY_DATA_RESEARCH.value
    ).status = TaskStatus.IN_PROGRESS

    model = initialize_model()
    tools = initialize_tools(model, execution_id, work_log)
    agents = initialize_agents(model, tools, work_log)

    in_memory_storage = tools["in_memory_storage_repo"]

    original_company_data = fetch_original_company_data(
        agents["search_agent"], company_name
    )

    work_log.get_single_task_with_key(
        TaskKeys.INITIAL_COMPANY_DATA_RESEARCH.value
    ).status = TaskStatus.COMPLETED
    work_log.get_single_task_with_key(
        TaskKeys.EXTRACT_DATA_FROM_RESEARCH_LOGS.value
    ).status = TaskStatus.IN_PROGRESS

    full_research_logs = str(in_memory_storage.retrieve_all())
    company_data_fetched_from_research_logs = process_in_memory_data(
        tools["process_in_memory_company_data_tool"],
        company_name,
        original_company_data,
        full_research_logs,
    )

    work_log.get_single_task_with_key(
        TaskKeys.EXTRACT_DATA_FROM_RESEARCH_LOGS.value
    ).status = TaskStatus.COMPLETED

    # Set the processed data as our working data
    final_company_data = company_data_fetched_from_research_logs

    if research_type == "comprehensive":
        # Run the comprehensive analysis pipeline
        work_log.get_single_task_with_key(
            TaskKeys.COMPUTE_FEEDBACK.value
        ).status = TaskStatus.IN_PROGRESS
        feedback_items = compute_feedback(
            tools["provide_feedback_company_data_tool"],
            company_name,
            final_company_data,
        )

        in_memory_storage.clear()

        work_log.get_single_task_with_key(
            TaskKeys.COMPUTE_FEEDBACK.value
        ).status = TaskStatus.COMPLETED
        work_log.get_single_task_with_key(
            TaskKeys.ADDRESS_FEEDBACK.value
        ).status = TaskStatus.IN_PROGRESS

        work_log.get_single_task_with_key(TaskKeys.ADDRESS_FEEDBACK.value).subtasks = []
        for i, feedback_item in enumerate(feedback_items):
            feedback_item_task = FlowTask(
                key=TaskKeys.FEEDBACK_ITEM.value + "_" + str(i),
                description=feedback_item,
                status=TaskStatus.PENDING,
            )
            if (
                work_log.get_single_task_with_key(
                    TaskKeys.ADDRESS_FEEDBACK.value
                ).subtasks
                is None
            ):
                work_log.get_single_task_with_key(
                    TaskKeys.ADDRESS_FEEDBACK.value
                ).subtasks = []
            task = work_log.get_single_task_with_key(TaskKeys.ADDRESS_FEEDBACK.value)
            if task.subtasks is not None:
                task.subtasks.append(feedback_item_task)

            feedback_item_research_task = FlowTask(
                key=TaskKeys.FEEDBACK_ITEM.value + "_" + str(i) + "_research",
                description="Searching for specific information to address current gap",
                status=TaskStatus.PENDING,
            )
            feedback_item_integrate_task = FlowTask(
                key=TaskKeys.FEEDBACK_ITEM.value + "_" + str(i) + "_integrate",
                description="Adding newly discovered information to the company profile",
                status=TaskStatus.PENDING,
            )
            feedback_item_task.subtasks = [
                feedback_item_research_task,
                feedback_item_integrate_task,
            ]

        for i, feedback_item in enumerate(feedback_items):
            work_log.get_single_task_with_key(
                TaskKeys.FEEDBACK_ITEM.value + "_" + str(i) + "_research"
            ).status = TaskStatus.IN_PROGRESS
            work_log.get_single_task_with_key(
                TaskKeys.FEEDBACK_ITEM.value + "_" + str(i)
            ).status = TaskStatus.IN_PROGRESS
            response_after_feedback = re_fetch_data_after_feedback(
                agents["re_fetch_data_after_feedback_agent"],
                company_name,
                feedback_item,
                final_company_data,
            )

            print("\n\n\n", "Original company data:", final_company_data)
            print("\n\n\n", "Requested feedback item:", feedback_item)
            print(
                "\n\n\n",
                "Response after research on feedback:",
                response_after_feedback,
            )

            work_log.get_single_task_with_key(
                TaskKeys.FEEDBACK_ITEM.value + "_" + str(i) + "_research"
            ).status = TaskStatus.COMPLETED
            work_log.get_single_task_with_key(
                TaskKeys.FEEDBACK_ITEM.value + "_" + str(i) + "_integrate"
            ).status = TaskStatus.IN_PROGRESS

            fixed_company_data = integrate_feedback(
                integrate_feedback_tool=tools["integrate_feedback_company_data_tool"],
                company_name=company_name,
                original_company_data=final_company_data,
                feedback=feedback_item,
                fixed_after_feedback=response_after_feedback,
                work_log=work_log,
            )
            work_log.get_single_task_with_key(
                TaskKeys.FEEDBACK_ITEM.value + "_" + str(i) + "_integrate"
            ).status = TaskStatus.COMPLETED
            work_log.get_single_task_with_key(
                TaskKeys.FEEDBACK_ITEM.value + "_" + str(i)
            ).status = TaskStatus.COMPLETED

            final_company_data = fixed_company_data

            print(
                "\n\n\n", "Response after feedback:", response_after_feedback, "\n\n\n"
            )
            print("\n\n\n", "Fixed company data:", fixed_company_data)

        work_log.get_single_task_with_key(
            TaskKeys.ADDRESS_FEEDBACK.value
        ).status = TaskStatus.COMPLETED

    # Generate the report regardless of the research type
    work_log.get_single_task_with_key(
        TaskKeys.GENERATE_REPORT.value
    ).status = TaskStatus.IN_PROGRESS

    print("--------------------------------")
    print("\n\n\n")
    print(final_company_data)
    print("\n\n\n")
    print("--------------------------------")
    print("\n\n\n")

    structured_company_data_xml = generate_structured_report(
        tools["generate_structured_company_data_report_tool"],
        model,
        company_name,
        final_company_data,
        work_log,
    )

    print("--------------------------------")
    print("\n\n\n")
    print(structured_company_data_xml)
    print("\n\n\n")
    print("--------------------------------")
    print("\n\n\n")

    html_report_path = generate_company_data_artifact(
        structured_company_data_xml, work_log.id
    )
    work_log.get_single_task_with_key(
        TaskKeys.GENERATE_REPORT.value
    ).status = TaskStatus.COMPLETED

    # Store the absolute path to the report file in the WorkLog
    work_log.report_file_path = html_report_path

    print("Html report saved to:", html_report_path)

    work_log.status = TaskStatus.COMPLETED

    return html_report_path


if __name__ == "__main__":
    # company_name = "BUA  Cement "
    # company_name = "OMOUR BEER PARLOUR AND KITCHEN"
    # company_name = "HARUNA WINE AND BEER STORES"
    # company_name = "MORABMORAVE GLOBAL MULTI PURPOSE VENTURES"
    task_group = create_work_log()
    company_name = "Mavin Records     "
    extract_company_data(company_name, "some_execution_id", task_group, "comprehensive")
