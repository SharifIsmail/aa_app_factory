from pathlib import Path

import pandas as pd
from smolagents import Tool

from evaluation.core.golden_dataset_manager import GoldenDatasetManager
from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)
from evaluation.golden_dataset_creation.setup import setup
from evaluation.intelligence_layer_eval.supplier_briefing_models import (
    QuestionDifficulty,
)
from service.agent_core.data_management.columns import (
    COL_BRUTTO_PRIORISIERUNG,
    COL_DATA_SOURCE,
    COL_GROUPING_FACHBEREICH,
    COL_KONKRETE_PRIORISIERUNG,
    COL_NETTO_PRIORISIERUNG,
    COL_REVENUE_TOTAL,
    COL_SCHWARZ_GROUP_FLAG,
    COL_SCHWARZBESCHAFFUNG,
)
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_preparation import BUSINESS_PARTNERS_PARQUET


def load_dataset_from_path(file_path: Path) -> pd.DataFrame:
    """Load dataset from parquet file."""
    return pd.read_parquet(file_path)


def split_comma_separated_rows(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Split rows where the specified column has comma-separated values into multiple rows.
    """
    if column_name not in df.columns:
        return df

    df_expanded = df.copy()
    comma_mask = df_expanded[column_name].astype(str).str.contains(",", na=False)

    if comma_mask.sum() == 0:
        return df_expanded

    df_expanded[column_name] = df_expanded[column_name].astype(str).str.split(",")
    df_expanded = df_expanded.explode(column_name)
    df_expanded[column_name] = df_expanded[column_name].str.strip()
    df_expanded = df_expanded.reset_index(drop=True)

    return df_expanded


def apply_bp_priority_filters(
    df: pd.DataFrame, min_revenue_threshold: float = 10000.0
) -> pd.DataFrame:
    """
    Apply business partner priority filters to the dataframe.
    Filters applied: revenue threshold, department exclusions (Schwarzbeschaffung),
    and child company exclusions (Schwarz group).
    """
    df_filtered = df.copy()

    filters_columns = {
        "revenue": COL_REVENUE_TOTAL,
        "schwarzbeschaffung": COL_SCHWARZBESCHAFFUNG,
        "schwarz_group": COL_SCHWARZ_GROUP_FLAG,
    }

    # CONDITION 1: Revenue threshold filter
    revenue_col = filters_columns["revenue"]
    if revenue_col and revenue_col in df_filtered.columns:
        clean_revenue_col = revenue_col + "_clean"

        if clean_revenue_col not in df_filtered.columns:
            df_filtered[clean_revenue_col] = pd.to_numeric(
                df_filtered[revenue_col], errors="coerce"
            )

        df_filtered = df_filtered[
            df_filtered[clean_revenue_col] >= min_revenue_threshold
        ]

    # CONDITION 2: Exclude Schwarzbeschaffung partners
    schwarzbeschaffung_col = filters_columns["schwarzbeschaffung"]
    if schwarzbeschaffung_col and schwarzbeschaffung_col in df_filtered.columns:
        schwarzbeschaffung_positive_values = ["x"]
        mask = ~df_filtered.loc[:, schwarzbeschaffung_col].isin(
            schwarzbeschaffung_positive_values
        )
        df_filtered = df_filtered.loc[mask].copy()

    # CONDITION 3: Exclude Schwarz group partners
    schwarz_group_col = filters_columns["schwarz_group"]
    if schwarz_group_col and schwarz_group_col in df_filtered.columns:
        schwarz_group_positive_values = ["X"]
        mask = ~df_filtered.loc[:, schwarz_group_col].isin(
            schwarz_group_positive_values
        )
        df_filtered = df_filtered.loc[mask].copy()

    return pd.DataFrame(df_filtered)


def create_priority_matrix(
    df: pd.DataFrame,
    priority_type: str = "Concrete",
    group_by: str = COL_GROUPING_FACHBEREICH,
) -> pd.DataFrame:
    """
    Create the business partner priority distribution matrix.
    """
    priority_columns = {
        "Netto": COL_NETTO_PRIORISIERUNG,
        "Concrete": COL_KONKRETE_PRIORISIERUNG,
        "Brutto": COL_BRUTTO_PRIORISIERUNG,
    }

    priority_col = priority_columns.get(priority_type)
    if not priority_col or priority_col not in df.columns:
        raise ValueError(f"Priority type '{priority_type}' not available.")

    if group_by not in df.columns:
        raise ValueError(f"Grouping column '{group_by}' not found in data.")

    working_df = df.copy()
    working_df = split_comma_separated_rows(working_df, group_by)

    valid_data = working_df.dropna(subset=[group_by, priority_col])

    if valid_data.empty:
        raise ValueError("No valid data found after removing null values")

    matrix = pd.crosstab(
        valid_data[group_by],
        valid_data[priority_col],
        margins=True,
        margins_name="Gesamtergebnis",
    )

    return matrix


def request_concrete_priority_by_department(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Geben Sie mir die Verteilung der Geschäftspartner auf Prioritätsebene, gruppiert nach Fachbereichsebenen."
    question_id = (
        "business_partner_priority_information_1_3_concrete_priority_by_department"
    )

    business_partners = load_dataset_from_path(DATA_DIR / BUSINESS_PARTNERS_PARQUET)
    df_filtered = apply_bp_priority_filters(business_partners)

    matrix = create_priority_matrix(
        df_filtered,
        priority_type="Concrete",
        group_by=COL_GROUPING_FACHBEREICH,
    )

    dataframes = [matrix]

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=dataframes,
        question_difficulty=QuestionDifficulty.EASY,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def request_concrete_priority_by_type_of_goods(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Geben Sie mir die Verteilung der Geschäftspartner auf Prioritätsebene, gruppiert nach Warentyp."
    question_id = (
        "business_partner_priority_information_2_3_concrete_priority_by_type_of_goods"
    )

    business_partners = load_dataset_from_path(DATA_DIR / BUSINESS_PARTNERS_PARQUET)
    df_filtered = apply_bp_priority_filters(business_partners)

    matrix = create_priority_matrix(
        df_filtered, priority_type="Concrete", group_by=COL_DATA_SOURCE
    )

    dataframes = [matrix]

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=dataframes,
        question_difficulty=QuestionDifficulty.EASY,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def create_business_partner_priority_examples() -> None:
    manager, tools = setup()

    request_concrete_priority_by_department(manager, tools)
    request_concrete_priority_by_type_of_goods(manager, tools)
