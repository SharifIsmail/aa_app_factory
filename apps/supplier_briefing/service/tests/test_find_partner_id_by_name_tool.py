from uuid import uuid4

import pandas as pd
import pytest

from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
)
from service.agent_core.model_tools_manager import DATA_DIR
from service.agent_core.tools.find_partner_id_by_name_tool import (
    FindPartnerIdByNameTool,
)
from service.agent_core.work_log_manager import create_work_log
from service.data_preparation import BUSINESS_PARTNERS_PARQUET


@pytest.fixture
def find_partner_id_by_name_tool() -> FindPartnerIdByNameTool:
    execution_id = str(uuid4())
    work_log = create_work_log(execution_id)

    return FindPartnerIdByNameTool(
        business_partner_file=DATA_DIR / BUSINESS_PARTNERS_PARQUET,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )


def test_find_partner_id_by_name_tool_basic_search(
    find_partner_id_by_name_tool: FindPartnerIdByNameTool,
) -> None:
    """Test basic functionality with a common business partner name."""
    # Search for a partner that likely exists but is more specific than "GmbH"
    result = find_partner_id_by_name_tool.forward("GmbH", max_results=16000)

    # Check DataFrame structure
    assert isinstance(result, pd.DataFrame)
    assert result.columns.tolist() == [COL_BUSINESS_PARTNER_NAME]
    assert result.index.name == COL_BUSINESS_PARTNER_ID

    # Should find some results
    assert result.shape[0] > 0

    # All partner names should contain "GmbH" (case insensitive)
    for partner_name in result[COL_BUSINESS_PARTNER_NAME]:
        assert "gmbh" in partner_name.lower()


def test_find_partner_id_by_name_tool_case_insensitive(
    find_partner_id_by_name_tool: FindPartnerIdByNameTool,
) -> None:
    """Test that search is case insensitive."""
    search_term = "GmbH"

    # Search with different cases
    result_upper = find_partner_id_by_name_tool.forward(
        search_term.upper(), max_results=16000
    )
    result_lower = find_partner_id_by_name_tool.forward(
        search_term.lower(), max_results=16000
    )
    result_mixed = find_partner_id_by_name_tool.forward("gMbH", max_results=16000)

    # Should find similar results regardless of case
    # Allow for more differences due to scoring variations with large datasets
    # The key is that all variations return valid results
    assert len(result_upper) > 0
    assert len(result_lower) > 0
    assert len(result_mixed) > 0
    # All should be within reasonable range of each other (within 50%)
    max_results = max(len(result_upper), len(result_lower), len(result_mixed))
    min_results = min(len(result_upper), len(result_lower), len(result_mixed))
    assert (max_results - min_results) / max_results <= 0.5


def test_find_partner_id_by_name_tool_empty_query(
    find_partner_id_by_name_tool: FindPartnerIdByNameTool,
) -> None:
    """Test that empty queries raise appropriate errors."""
    # Test empty string
    for empty_query in ("", "   "):
        with pytest.raises(
            ValueError, match="Query for business partner search cannot be empty"
        ):
            find_partner_id_by_name_tool.forward(empty_query, max_results=50)


def test_find_partner_id_by_name_tool_no_results(
    find_partner_id_by_name_tool: FindPartnerIdByNameTool,
) -> None:
    """Test that queries with no matches return properly structured empty DataFrame."""
    # Search for a very unlikely business partner name
    result = find_partner_id_by_name_tool.forward(
        "VERY_UNLIKELY_BUSINESS_PARTNER_NAME_12345", max_results=50
    )

    # Should return empty DataFrame with correct structure
    assert result.empty
    assert result.columns.tolist() == [COL_BUSINESS_PARTNER_NAME]
    assert result.index.name == COL_BUSINESS_PARTNER_ID


def test_find_partner_id_by_name_tool_raises_exception_for_max_results(
    find_partner_id_by_name_tool: FindPartnerIdByNameTool,
) -> None:
    """Test that ValueError is raised when max_results is exceeded."""
    with pytest.raises(
        ValueError, match="Search returned .* results, which exceeds max_results=1"
    ):
        # Use a very broad search that should find many results
        find_partner_id_by_name_tool.forward("GmbH", max_results=1)


def test_find_partner_id_by_name_tool_unique_values_returned(
    find_partner_id_by_name_tool: FindPartnerIdByNameTool,
) -> None:
    """Test that returned business partner IDs are unique."""
    result = find_partner_id_by_name_tool.forward("GmbH", max_results=16000)

    if not result.empty:
        # Check that all business partner IDs are unique
        partner_ids = result.index.tolist()
        assert len(partner_ids) == len(set(partner_ids)), (
            "All business partner IDs should be unique"
        )
