from uuid import uuid4

import pytest

from service.agent_core.constants import REPO_PANDAS_OBJECTS
from service.agent_core.data_management.columns import COL_ARTIKELFAMILIE
from service.agent_core.data_management.data_documentation import DataDocumentation
from service.agent_core.tools.inspect_column_values_tool import InspectColumnValuesTool
from service.agent_core.work_log_manager import create_work_log
from service.data_preparation import TRANSACTIONS_PARQUET


@pytest.fixture
def inspect_column_values() -> InspectColumnValuesTool:
    execution_id = str(uuid4())
    work_log = create_work_log(execution_id)

    return InspectColumnValuesTool(
        data_files=DataDocumentation.get_all_data_files_with_descriptions(),
        data_storage=work_log.data_storage,
        work_log=work_log,
        execution_id=execution_id,
        repo_key=REPO_PANDAS_OBJECTS,
    )


def test_find_category_or_product(
    inspect_column_values: InspectColumnValuesTool,
) -> None:
    # There are more than 1000 unique values in COL_ARTIKELFAMILIE
    column_values = inspect_column_values(
        column_name=COL_ARTIKELFAMILIE,
        dataset_name=TRANSACTIONS_PARQUET,
        max_values=2000,
    )
    assert isinstance(column_values, list)
    for value in column_values:
        assert isinstance(value, str)
    assert "WASSER" in column_values


def test_find_category_or_product_raises_exception_for_max_results(
    inspect_column_values: InspectColumnValuesTool,
) -> None:
    with pytest.raises(RuntimeError):
        # There are more than 1000 unique values in COL_ARTIKELFAMILIE
        inspect_column_values(
            column_name=COL_ARTIKELFAMILIE,
            dataset_name=TRANSACTIONS_PARQUET,
            max_values=1000,
        )
