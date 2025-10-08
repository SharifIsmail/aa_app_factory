from uuid import uuid4

import pytest

from service.agent_core.model_tools_manager import DATA_DIR
from service.agent_core.tools.find_branches_tool import (
    BranchNotFoundError,
    FindBranchesTool,
    Sector,
)
from service.agent_core.work_log_manager import create_work_log


@pytest.fixture
def find_branches_tool() -> FindBranchesTool:
    execution_id = str(uuid4())
    work_log = create_work_log(execution_id)

    return FindBranchesTool(
        risk_per_branch_file=DATA_DIR / "transactions.parquet",
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )


def test_find_branches_sugar_refining(
    find_branches_tool: FindBranchesTool,
) -> None:
    """Test search for 'sugar refining' should return only 'D 08 SUGAR REFINING' sector."""
    result = find_branches_tool.forward("sugar refining")

    # Check result structure
    assert isinstance(result, dict)
    assert Sector.SECTOR_DETAILLIERT in result
    assert Sector.SECTOR_GROB in result

    # Should be only the expected sugar refining sector
    sugar_refining_sector = "D 08 SUGAR REFINING"
    assert result == {
        Sector.SECTOR_DETAILLIERT: [sugar_refining_sector],
        Sector.SECTOR_GROB: [sugar_refining_sector],
    }


def test_find_branches_craftsmanship(
    find_branches_tool: FindBranchesTool,
) -> None:
    """Test search for 'craftsmanship' should return multiple values."""
    result = find_branches_tool.forward("craftsmanship")

    # Check result structure
    assert isinstance(result, dict)
    assert Sector.SECTOR_DETAILLIERT in result
    assert Sector.SECTOR_GROB in result

    # Should find multiple results for craftsmanship
    all_results = result[Sector.SECTOR_DETAILLIERT] + result[Sector.SECTOR_GROB]  # type: ignore
    assert len(all_results) > 1, "Craftsmanship search should return multiple sectors"


def test_find_branches_construction(
    find_branches_tool: FindBranchesTool,
) -> None:
    """Test search for 'construction' should return 'F 01 CONSTRUCTION' sector."""
    result = find_branches_tool.forward("construction")

    # Check result structure
    assert isinstance(result, dict)
    assert Sector.SECTOR_DETAILLIERT in result
    assert Sector.SECTOR_GROB in result

    # Should find construction-related sectors
    all_results = result[Sector.SECTOR_DETAILLIERT] + result[Sector.SECTOR_GROB]  # type: ignore
    assert len(all_results) > 0

    # Should contain the expected construction sector
    construction_sectors = [
        sector for sector in all_results if "CONSTRUCTION" in sector.upper()
    ]
    assert len(construction_sectors) > 0
    assert any("F 01 CONSTRUCTION" in sector for sector in construction_sectors)


def test_find_branches_max_results_exceeded(
    find_branches_tool: FindBranchesTool,
) -> None:
    """Test that low max_results value throws appropriate error when exceeded."""
    with pytest.raises(ValueError, match="exceeds max_results"):
        # Use a broad search term that should find many results
        find_branches_tool.forward("manufacturing", max_results=1)


def test_find_branches_empty_search_term(
    find_branches_tool: FindBranchesTool,
) -> None:
    """Test that empty search terms raise appropriate errors."""
    # Test empty string
    with pytest.raises(ValueError, match="Search term cannot be empty"):
        find_branches_tool.forward("")

    # Test whitespace only
    with pytest.raises(ValueError, match="Search term cannot be empty"):
        find_branches_tool.forward("   ")


def test_find_branches_no_results(
    find_branches_tool: FindBranchesTool,
) -> None:
    """Test that search terms with no matches raise appropriate error."""
    # Search for a very unlikely term
    with pytest.raises(
        BranchNotFoundError, match="No branch names found for the search term"
    ):
        find_branches_tool.forward("VERY_UNLIKELY_BRANCH_NAME_12345")
