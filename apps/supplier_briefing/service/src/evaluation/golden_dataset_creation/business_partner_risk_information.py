from typing import cast

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
    COL_RISKIEST_RESOURCE_KONKRET,
)


def request_1_0_risk_matrix_business_partner(
    manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    bp_risk_tool = tools["business_partner_risk_tool"]
    risk_matrix = bp_risk_tool("1514", risk_type="Konkretes Risiko", risk_tier=None)

    manager.add_entry(
        research_question="Welche Risikoinformationen liegen uns zum Geschäftspartner mit der ID 1514 vor?",
        question_id="business_partner_risk_information__1_0__risk_matrix_business_partner",
        ground_truth_text=None,
        pandas_objects=[risk_matrix],
        question_difficulty=QuestionDifficulty.EASY,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def request_2_1_riskiest_resources_business_partner(
    manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    df_tool = tools["pandas_dataframe_tool"]
    transactions = df_tool("transactions")
    transactions = cast(pd.DataFrame, transactions)

    bp_transactions = transactions[transactions[COL_BUSINESS_PARTNER_ID] == "1514"]
    bp_transactions = cast(pd.DataFrame, bp_transactions)

    concrete_riskiest_resource_col = COL_RISKIEST_RESOURCE_KONKRET

    riskiest_resources = bp_transactions[concrete_riskiest_resource_col].unique()
    riskiest_resources = [
        resource for resource in riskiest_resources if resource is not None
    ]
    riskiest_resources_df = pd.DataFrame(
        riskiest_resources,
        columns=[concrete_riskiest_resource_col],
    )

    manager.add_entry(
        research_question="Geben Sie mir die riskantesten Rohstoffe für den Geschäftspartner mit der ID 1514",
        question_id="business_partner_risk_information__2_1_riskiest_resources_business_partner",
        ground_truth_text=None,
        pandas_objects=[riskiest_resources_df],
        question_difficulty=QuestionDifficulty.EASY,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def request_2_2_articles_business_partner(
    manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    get_business_partner_products_tool = tools["get_business_partner_products"]
    products_from_bp_df = get_business_partner_products_tool("1514")

    manager.add_entry(
        research_question="Welche Aritkel beziehen wir von dem Geschäftspartner mit der ID 1514?",
        question_id="business_partner_risk_information__2_2_articles_business_partner",
        ground_truth_text=None,
        pandas_objects=[products_from_bp_df],
        question_difficulty=QuestionDifficulty.EASY,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def create_business_partner_risk_information_examples() -> None:
    manager, tools = setup()

    request_1_0_risk_matrix_business_partner(manager, tools)
    request_2_1_riskiest_resources_business_partner(manager, tools)
    request_2_2_articles_business_partner(manager, tools)
