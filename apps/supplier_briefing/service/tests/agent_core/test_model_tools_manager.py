from uuid import uuid4

from service.agent_core.initialize_models import initialize_models
from service.agent_core.model_tools_manager import initialize_tools
from service.agent_core.work_log_manager import create_work_log
from service.dependencies import with_settings


def test_initialize_tools_runnable() -> None:
    models = initialize_models()
    execution_id = str(uuid4())
    work_log = create_work_log(execution_id)
    settings = with_settings()

    initialize_tools(
        models,
        execution_id,
        work_log,
        settings,
    )
