from datetime import datetime

import pandas as pd
from smolagents import Tool

from evaluation.core.golden_dataset_manager import GoldenDatasetManager
from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)
from evaluation.golden_dataset_creation.setup import setup
from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_GROUPING_FACHBEREICH,
)
from service.agent_core.data_management.transactions import Transactions


def overlaps_with_target_period(
    start_date_str: str, end_date_str: str, target_start: datetime, target_end: datetime
) -> bool:
    """Check if a date range overlaps with the target period."""
    range_start = datetime.strptime(start_date_str, "%m/%Y")
    range_end = datetime.strptime(end_date_str, "%m/%Y")

    if range_start is None or range_end is None:
        return False

    # Check for overlap: ranges overlap if start1 <= end2 and start2 <= end1
    return range_start <= target_end and target_start <= range_end


def contains_keyword(value: str, keyword: str) -> bool:
    """Check if value contains keyword (case insensitive)."""
    if pd.isna(value):
        return False

    return keyword.lower() in value.lower()


def request_1_1_business_partner_count_by_temporal_context(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Wieviele Geschäftspartner haben wir in unseren Daten?"
    question_id = (
        "business_partner_numbers__1_1_business_partner_count_by_temporal_context"
    )

    # Generate ground truth answer
    transactions = Transactions.df()

    total_business_partners = transactions[COL_BUSINESS_PARTNER_ID].nunique()

    # Assemble expected output
    ground_truth_text = f"Es wurden {total_business_partners} Geschäftspartner in den Daten identifiziert."

    # Add to golden dataset
    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=ground_truth_text,
        pandas_objects=[],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def request_2_1_business_partner_count_by_department_immobilien(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Wieviele Geschäftspartner haben wir im Fachbereich Immobilien?"
    question_id = (
        "business_partner_numbers__2_1_business_partner_count_by_department_immobilien"
    )

    # Generate ground truth answer
    transactions = Transactions.df()

    immo_mask = transactions[COL_GROUPING_FACHBEREICH].apply(
        lambda x: contains_keyword(x, "immo")
    )

    transactions_filtered = transactions[immo_mask]
    total_business_partners = transactions_filtered[COL_BUSINESS_PARTNER_ID].nunique()

    ground_truth_text = f"Im Fachbereich Immobilien haben wir {total_business_partners} Geschäftspartner identifiziert."

    # Add to golden dataset
    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=ground_truth_text,
        pandas_objects=[],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def create_business_partner_numbers_examples() -> None:
    manager, tools = setup()

    request_1_1_business_partner_count_by_temporal_context(manager, tools)
    request_2_1_business_partner_count_by_department_immobilien(manager, tools)
