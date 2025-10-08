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
    COL_COUNTRY,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_PLACE_OF_PRODUCTION_ID,
    COL_PLACE_OF_PRODUCTION_NAME,
)
from service.agent_core.data_management.transactions import Transactions
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path
from service.data_preparation import BUSINESS_PARTNERS_PARQUET


def request_1_bps_from_france_and_in_sugar_refining_branch(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = 'Wie viele Geschäftspartner haben wir in Frankreich, die in der Branche "D 08 SUGAR REFINING" tätig sind?'
    question_id = (
        "feedback_2025_09_11_request_1_bps_from_france_and_in_sugar_refining_branch"
    )

    bp_df = load_dataset_from_path(DATA_DIR / BUSINESS_PARTNERS_PARQUET)

    france_filter = bp_df[COL_COUNTRY] == "FRA"

    # We need to filter for the sector only as partial str match, because a business partner can have multiple branches (as a comma separated list)
    sugar_refining_filter = bp_df[COL_ESTELL_SEKTOR_GROB_RENAMED].str.contains(
        "D 08 SUGAR REFINING"
    )

    bps_from_france_and_in_sugar_refining = bp_df[france_filter & sugar_refining_filter]
    count = len(bps_from_france_and_in_sugar_refining)

    ground_truth_text = f"Es gibt {count} Geschäftspartner in Frankreich, die in der Branche 'D 08 SUGAR REFINING' tätig sind."

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=ground_truth_text,
        pandas_objects=[],
        question_difficulty=QuestionDifficulty.HARD,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def request_2_production_sites_of_business_partner(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = 'Gib mir eine Liste der Produktionsstätten des Geschäftspartners „NetIoT Networks UG" mit der ID 11472?'
    question_id = "feedback_2025_09_11_request_2_production_sites_of_business_partner"

    # We need to use the transactions data because it contains production site details
    transactions_df = Transactions.df()

    # Filter for the specific business partner by ID and name
    partner_id_filter = transactions_df[COL_BUSINESS_PARTNER_ID] == "11472"
    partner_id_transactions = transactions_df[partner_id_filter]

    # Get unique production sites for this business partner
    production_sites = (
        partner_id_transactions[
            [COL_PLACE_OF_PRODUCTION_ID, COL_PLACE_OF_PRODUCTION_NAME]
        ]
        .drop_duplicates()
        .dropna()
    )

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[production_sites],
        question_difficulty=QuestionDifficulty.HARD,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=True,
            ignore_column_names=True,
        ),
    )


def create_feedback_2025_09_11_examples() -> None:
    manager, _ = setup()
    request_1_bps_from_france_and_in_sugar_refining_branch(manager)
    request_2_production_sites_of_business_partner(manager)


if __name__ == "__main__":
    create_feedback_2025_09_11_examples()
