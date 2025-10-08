from uuid import uuid4

import pytest

from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_COUNTRY,
    COL_GEFUNDENE_RISIKOROHSTOFFE,
)
from service.agent_core.model_tools_manager import transaction_file
from service.agent_core.tools.find_natural_resource_tool import (
    FindNaturalResourcesPerPartnerTool,
)
from service.agent_core.work_log_manager import create_work_log


@pytest.fixture
def find_natural_resource_tool() -> FindNaturalResourcesPerPartnerTool:
    execution_id = str(uuid4())
    work_log = create_work_log(execution_id)

    return FindNaturalResourcesPerPartnerTool(
        transactions_file=transaction_file,
        data_storage=work_log.data_storage,
        work_log=work_log,
        execution_id=execution_id,
    )


def test_find_natural_resource_basic_search(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test basic functionality with query for a common resource."""
    result = find_natural_resource_tool(resource_query="HOLZ", max_results=15000)

    # Check DataFrame structure
    assert result.columns.tolist() == [
        COL_BUSINESS_PARTNER_NAME,
        COL_COUNTRY,
        COL_GEFUNDENE_RISIKOROHSTOFFE,
    ]
    assert result.index.name == COL_BUSINESS_PARTNER_ID

    assert result.shape[0] > 0

    for resources in result[COL_GEFUNDENE_RISIKOROHSTOFFE]:
        assert "HOLZ" in resources.upper()


def test_find_natural_resource_with_country_filter(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test filtering by country code."""
    # Search for resources from a specific country
    result = find_natural_resource_tool(
        resource_query="HOLZ", country_code="DEU", max_results=5000
    )

    # Check that all results are from the specified country
    if not result.empty:
        for country in result[COL_COUNTRY]:
            assert country.upper() == "DEU"


def test_find_natural_resource_empty_result(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test that empty results return properly structured DataFrame."""
    # Search for a very unlikely resource pattern
    result = find_natural_resource_tool(
        resource_query="VERY_UNLIKELY_RESOURCE_NAME", max_results=50
    )

    # Should return empty DataFrame with correct structure
    assert result.empty
    assert result.columns.tolist() == [
        COL_BUSINESS_PARTNER_NAME,
        COL_COUNTRY,
        COL_GEFUNDENE_RISIKOROHSTOFFE,
    ]
    assert result.index.name == COL_BUSINESS_PARTNER_ID


def test_find_natural_resource_case_insensitive(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test that search is case insensitive."""
    # Search with different cases
    result_upper = find_natural_resource_tool(resource_query="HOLZ", max_results=15000)
    result_lower = find_natural_resource_tool(resource_query="holz", max_results=15000)
    result_mixed = find_natural_resource_tool(resource_query="Holz", max_results=15000)

    # All should return the same number of results
    assert len(result_upper) == len(result_lower) == len(result_mixed)


def test_find_natural_resource_max_results_exception(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test that RuntimeError is raised when max_results is exceeded."""
    with pytest.raises(RuntimeError, match="Number of results .* exceeds the limit"):
        # Use a very common query that should find many results
        find_natural_resource_tool(resource_query="HOLZ", max_results=1)


def test_find_natural_resource_resource_deduplication(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test that duplicate resources are properly deduplicated per business partner."""
    result = find_natural_resource_tool(resource_query="HOLZ", max_results=15000)

    # Check that resources are properly formatted and deduplicated
    if not result.empty:
        for resources in result[COL_GEFUNDENE_RISIKOROHSTOFFE]:
            # Resources should be joined with '/'
            resource_list = resources.split("/")
            # No duplicates should exist
            assert len(resource_list) == len(set(resource_list))


def test_find_natural_resource_invalid_country_code(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test filtering with non-existent country code returns empty result."""
    result = find_natural_resource_tool(
        resource_query="HOLZ", country_code="XYZ", max_results=50
    )

    # Should return empty DataFrame
    assert result.empty
    assert result.index.name == COL_BUSINESS_PARTNER_ID


def test_find_natural_resource_none_max_results(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test that max_results=None uses the default value."""
    # This should not raise an exception even with broad patterns
    result = find_natural_resource_tool(resource_query="HOLZ", max_results=None)

    # Should return some results without raising an exception
    assert isinstance(result.index.name, str)
    assert result.index.name == COL_BUSINESS_PARTNER_ID


def test_find_natural_resource_common_resources(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Test searching for common natural resources that are likely to exist."""
    common_resources = ["WASSER", "HOLZ", "BAUMWOLLE"]

    for resource_query in common_resources:
        result = find_natural_resource_tool(
            resource_query=resource_query, max_results=15000
        )

        # Check basic structure regardless of whether results are found
        assert result.index.name == COL_BUSINESS_PARTNER_ID
        assert set(result.columns) == {
            COL_BUSINESS_PARTNER_NAME,
            COL_COUNTRY,
            COL_GEFUNDENE_RISIKOROHSTOFFE,
        }
        # Check that results are found
        assert result.shape[0] > 0


def test_find_natural_resource_rejects_empty_query(
    find_natural_resource_tool: FindNaturalResourcesPerPartnerTool,
) -> None:
    """Ensure empty query is rejected with a clear ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        find_natural_resource_tool(resource_query="", max_results=10)
