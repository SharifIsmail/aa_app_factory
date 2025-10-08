from uuid import uuid4

from smolagents import Tool

from evaluation.core.golden_dataset_manager import GoldenDatasetManager
from service.agent_core.initialize_models import initialize_models
from service.agent_core.model_tools_manager import initialize_tools
from service.agent_core.work_log_manager import create_work_log
from service.dependencies import with_settings


def setup() -> tuple[GoldenDatasetManager, dict[str, Tool]]:
    models = initialize_models()
    execution_id = str(uuid4())
    work_log = create_work_log(execution_id)
    settings = with_settings()

    tools = initialize_tools(
        models,
        execution_id,
        work_log,
        settings,
    )

    manager = GoldenDatasetManager()
    return manager, tools
