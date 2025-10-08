import litellm
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel

from service.dependencies import with_settings
from service.law_core.llm.aleph_alpha_llm_provider import AALLMProvider
from service.law_core.models import WorkLog
from service.law_core.tools.fetch_webpage_div_content import FetchWebpageDivContentTool
from service.law_core.tools.llm_completion_tool import LLMCompletionTool
from service.storage.in_memory_storage import InMemoryStorage

# Repository keys for law monitoring data
REPO_LAW_DATA = "LAW_DATA"
REPO_EXTRACTED_DATA = "EXTRACTED_DATA"


def initialize_model() -> LiteLLMModel:
    """Initialize the LiteLLM model with Aleph Alpha provider."""
    # Ensure environment variables are loaded before creating provider
    load_dotenv(verbose=True)
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


def llama33_70b() -> LiteLLMModel:
    """Initialize the LiteLLM model with Aleph Alpha provider for Llama3.3 70B"""
    load_dotenv(verbose=True)
    settings = with_settings()
    model_id = f"aleph-alpha/llama-3.3-70b-instruct"
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


def initialize_tools(
    lite_llm_model: LiteLLMModel, execution_id: str, work_log: WorkLog
) -> dict:
    """Initialize tools for law monitoring and analysis."""
    # Define repositories for law monitoring data
    work_log.data_storage.define_repo(REPO_LAW_DATA)
    work_log.data_storage.define_repo(REPO_EXTRACTED_DATA)

    in_memory_storage = InMemoryStorage()

    fetch_webpage_content_tool = FetchWebpageDivContentTool(
        execution_id=execution_id,
        work_log=work_log,
        repo_key=REPO_LAW_DATA,
        data_storage=in_memory_storage,
    )
    llm_completion_tool = LLMCompletionTool(
        lite_llm_model=lite_llm_model, execution_id=execution_id, work_log=work_log
    )

    return {
        "in_memory_storage_repo": in_memory_storage,
        "fetch_webpage_content_tool": fetch_webpage_content_tool,
        "llm_completion_tool": llm_completion_tool,
    }


def initialize_agents(
    model: LiteLLMModel, tools: dict, work_log: WorkLog
) -> dict[str, CodeAgent]:
    """Initialize agents for law monitoring tasks."""

    return {}
