from uuid import uuid4

import pytest

from service.agent_core.model_tools_manager import transaction_file
from service.agent_core.tools.find_category_or_product_tool import (
    FindCategoryOrProductTool,
)
from service.agent_core.work_log_manager import create_work_log


@pytest.fixture
def find_category_or_product() -> FindCategoryOrProductTool:
    execution_id = str(uuid4())
    work_log = create_work_log(execution_id)

    return FindCategoryOrProductTool(
        transaction_file=transaction_file,
        data_storage=work_log.data_storage,
        work_log=work_log,
        execution_id=execution_id,
    )


def test_find_category_or_product(
    find_category_or_product: FindCategoryOrProductTool,
) -> None:
    categories_trauben = find_category_or_product("Trauben", max_results=150)
    assert categories_trauben.columns.tolist() == ["value", "column_name"]
    for value in categories_trauben["value"]:
        assert "TRAUBEN" in value.upper()
    assert categories_trauben.shape[0] == 1


def test_find_category_or_product_raises_exception_for_max_results(
    find_category_or_product: FindCategoryOrProductTool,
) -> None:
    with pytest.raises(RuntimeError):
        find_category_or_product("Whiskey", max_results=1)


def test_find_category_or_product_case_insensitive(
    find_category_or_product: FindCategoryOrProductTool,
) -> None:
    """Test that search is case-insensitive."""
    # Search with different cases
    result_upper = find_category_or_product("TRAUBEN", max_results=150)
    result_lower = find_category_or_product("trauben", max_results=150)
    result_mixed = find_category_or_product("Trauben", max_results=150)

    # All should return the same number of results
    assert len(result_upper) == len(result_lower) == len(result_mixed)
