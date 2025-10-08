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
from service.agent_core.data_management.columns import COL_BUSINESS_PARTNER_NAME
from service.agent_core.model_tools_manager import DATA_DIR
from service.agent_core.tools.summarize_business_partner_tool import (
    BUSINESS_PARTNER_SUMMARY_COLUMNS,
)
from service.data_loading import load_dataset_from_path
from service.data_preparation import BUSINESS_PARTNERS_PARQUET

golden_dataset_manager = GoldenDatasetManager()


def request_1_0_business_partner_search_exists_by_name(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = 'Haben wir einen Geschäftspartner mit dem Namen "GlobalMarketing Network" in unseren Daten?'
    question_id = "business_partner_search__1_0_search_exists_by_name"

    # Generate ground truth answer
    business_partners = load_dataset_from_path(DATA_DIR / BUSINESS_PARTNERS_PARQUET)
    matching_business_partners = business_partners[
        business_partners[COL_BUSINESS_PARTNER_NAME].str.contains(
            "GlobalMarketing Network", regex=True, na=False
        )
    ]
    matching_business_partners_only_name_column = matching_business_partners[
        [COL_BUSINESS_PARTNER_NAME]
    ]

    # Assemble expected output
    ground_truth_text = (
        "Es gibt mehrere Geschäftspartner, die zu diesem Suchbegriff passen."
    )
    dataframes = [matching_business_partners_only_name_column]

    # Add to golden dataset
    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=ground_truth_text,
        pandas_objects=dataframes,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SCORE_OVERLAP,
            drop_index=True,
            ignore_column_names=True,
        ),
    )


def request_2_1_business_partner_search_information_retrieval(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    business_partner_id = "25120"
    business_partner_name = "GlobalMarketing Networks UG"
    question = f'Gib mir eine Übersicht über den Lieferanten "{business_partner_name}" mit der ID "{business_partner_id}"'
    question_id = "business_partner_search__2_1_search_information_retrieval"

    # Generate ground truth answer
    business_partners = load_dataset_from_path(DATA_DIR / BUSINESS_PARTNERS_PARQUET)
    matching_business_partner = business_partners.loc[business_partner_id]

    matching_business_partner_summary_columns = matching_business_partner[
        BUSINESS_PARTNER_SUMMARY_COLUMNS
    ]

    # Assemble expected output
    ground_truth_text = None
    dataframes = [matching_business_partner_summary_columns]

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


def create_business_partner_search_examples() -> None:
    manager, tools = setup()

    request_1_0_business_partner_search_exists_by_name(manager, tools)
    request_2_1_business_partner_search_information_retrieval(manager, tools)
