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
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_COUNTRY,
    COL_GEFUNDENE_RISIKOROHSTOFFE,
    COL_RISIKOROHSTOFFE,
)
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path
from service.data_preparation import TRANSACTIONS_PARQUET

# Use constants from columns.py
COL_RISK_RESOURCES = COL_RISIKOROHSTOFFE
COL_COUNTRY_ORIGIN = COL_COUNTRY


def request_1_0_natural_resource_search_bauxit_germany(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Beziehen wir Bauxit von einem Geschäftspartner in Deutschland?"
    question_id = "natural_resource_search__1_0_bauxit_germany"

    # Generate ground truth answer by simulating what the tool would return
    transactions_df = load_dataset_from_path(
        DATA_DIR / TRANSACTIONS_PARQUET,
        columns=[
            COL_BUSINESS_PARTNER_ID,
            COL_BUSINESS_PARTNER_NAME,
            COL_COUNTRY_ORIGIN,
            COL_RISK_RESOURCES,
        ],
    )

    # Filter for Germany
    germany_df = transactions_df[transactions_df[COL_COUNTRY_ORIGIN] == "DEU"].copy()

    # Split and explode resources on '/' while preserving original casing
    germany_df[COL_RISK_RESOURCES] = (
        germany_df[COL_RISK_RESOURCES].fillna("").astype(str)
    )
    germany_df = germany_df.assign(
        **{COL_RISK_RESOURCES: germany_df[COL_RISK_RESOURCES].str.split("/")}
    ).explode(COL_RISK_RESOURCES, ignore_index=True)
    germany_df[COL_RISK_RESOURCES] = (
        germany_df[COL_RISK_RESOURCES].astype(str).str.strip()
    )
    germany_df = germany_df[germany_df[COL_RISK_RESOURCES] != ""]

    # Match BAUXIT case-insensitively
    mask = germany_df[COL_RISK_RESOURCES].str.contains("BAUXIT", case=False, na=False)
    bauxit_matches = germany_df[mask]

    # Deduplicate by partner and resource
    unique_matches = bauxit_matches.drop_duplicates(
        subset=[COL_BUSINESS_PARTNER_ID, COL_RISK_RESOURCES]
    )

    aggregated = (
        unique_matches.sort_values(by=COL_BUSINESS_PARTNER_ID)
        .groupby(COL_BUSINESS_PARTNER_ID, as_index=True)
        .apply(
            lambda group: pd.Series(
                {
                    COL_BUSINESS_PARTNER_NAME: group[COL_BUSINESS_PARTNER_NAME].iloc[0],
                    COL_COUNTRY_ORIGIN: group[COL_COUNTRY_ORIGIN].iloc[0],
                    COL_GEFUNDENE_RISIKOROHSTOFFE: "/".join(group[COL_RISK_RESOURCES]),
                }
            )
        )
    )

    # Assemble expected output
    ground_truth_text = f"Ja, wir beziehen Bauxit von Geschäftspartnern aus Deutschland. Die Ergebnisse sind in der Tabelle zu finden."
    dataframes = [aggregated]

    # Add to golden dataset
    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=ground_truth_text,
        pandas_objects=dataframes,
        question_difficulty=QuestionDifficulty.EASY,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SCORE_OVERLAP,
            drop_index=True,
            ignore_column_names=True,
        ),
    )


def create_natural_resource_search_examples() -> None:
    manager, tools = setup()

    request_1_0_natural_resource_search_bauxit_germany(manager, tools)


if __name__ == "__main__":
    create_natural_resource_search_examples()
