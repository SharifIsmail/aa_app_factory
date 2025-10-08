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
    COL_ARTIKELFAMILIE,
    COL_COUNTRY,
    COL_LAENDERHERKUENFTE,
    COL_ROHSTOFFNAME,
)
from service.agent_core.data_management.transactions import Transactions
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path


def request_1_0_country_origin_grapes_from_india(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Beziehen wir Trauben von Geschäftspartnern aus Indien?"
    question_id = "country_origin__1_0_grapes_from_india"

    ground_truth_text = "Keiner unserer Geschäftspartner bezieht Trauben aus Indien."
    dataframes: list[pd.DataFrame] = []

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=ground_truth_text,
        pandas_objects=dataframes,
        question_difficulty=QuestionDifficulty.EASY,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def request_1_1_country_origin_grapes_which_countries(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Aus welchen Ländern beziehen wir Trauben?"
    question_id = "country_origin__1_1_grapes_which_countries"

    transcations = Transactions.df()
    mask = transcations[COL_ARTIKELFAMILIE].isin(["TRAUBEN"])
    results = transcations.loc[mask].drop_duplicates()

    countries_series = results[COL_COUNTRY].drop_duplicates().reset_index(drop=True)

    dataframes = [countries_series]

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=dataframes,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=True,
            ignore_column_names=True,
        ),
    )


def request_2_1_country_origin_grapes_risk_profile(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Ich benötige ein Risikoprofil des Rohstoffs Trauben."
    question_id = "country_origin__2_1_grapes_risk_profile"

    resource_risks = load_dataset_from_path(
        DATA_DIR / "resource_risks_processed.parquet"
    )

    mask = resource_risks[COL_ROHSTOFFNAME].isin(["TRAUBEN"])
    results = resource_risks.loc[mask].drop_duplicates()

    base_columns = [COL_ROHSTOFFNAME, COL_LAENDERHERKUENFTE]
    risk_columns = [
        col for col in resource_risks.columns if col.startswith("Brutto-Risiko")
    ]
    relevant_columns = base_columns + risk_columns

    result_df = results[relevant_columns]

    dataframes = [result_df]

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


def request_2_2_country_origin_product_from_india(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Welche Produkte beziehen wir von Geschäftspartnern aus Indien?"
    question_id = "country_origin__2_2_product_from_india"

    get_products_by_country_tool = tools["get_products_by_country"]

    products_from_india_df = get_products_by_country_tool(
        "IND", include_trading_goods_only=True
    )

    dataframes = [products_from_india_df]

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


def create_country_origin_examples() -> None:
    manager, tools = setup()

    request_1_0_country_origin_grapes_from_india(manager, tools)
    request_1_1_country_origin_grapes_which_countries(manager, tools)
    request_2_1_country_origin_grapes_risk_profile(manager, tools)
    request_2_2_country_origin_product_from_india(manager, tools)
