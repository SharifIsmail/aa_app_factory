from smolagents import Tool

from evaluation.core.golden_dataset_manager import GoldenDatasetManager
from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)
from evaluation.golden_dataset_creation.setup import setup
from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_COUNTRY,
)
from service.agent_core.data_management.transactions import Transactions


def request_1_1_business_partner_distribution_by_country(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = (
        "Gib mir die Verteilung der Geschäftspartner nach Ländern. Die "
        'Länderspalte soll "Länder" heißen und die Spalte mit der Anzahl der '
        'verschiedenen Geschäftspartner soll "Anzahl GP" heißen.'
        "Die Tabelle soll absteigend nach der Anzahl der Geschäftspartner "
        "sortiert sein."
    )
    question_id = (
        "business_partner_distribution_1_1_business_partner_distribution_by_country"
    )

    # load data from business_partners.parquet
    transactions = Transactions.df()

    # create a dataframe with the country and the number of business partners
    unique_bp_country = transactions[
        [COL_BUSINESS_PARTNER_ID, COL_COUNTRY]
    ].drop_duplicates()
    bp_distribution = (
        unique_bp_country.groupby(COL_COUNTRY)
        .size()
        .reset_index(name="business_partner_count")
    )
    bp_distribution = bp_distribution.sort_values(
        by="business_partner_count", ascending=False
    ).rename(
        columns={
            COL_COUNTRY: "Länder",
            "business_partner_count": "Anzahl GP",
        }
    )

    # Add to golden dataset
    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[bp_distribution],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=True,
        ),
    )


def create_business_partner_distribution_examples() -> None:
    manager, tools = setup()

    request_1_1_business_partner_distribution_by_country(manager, tools)
