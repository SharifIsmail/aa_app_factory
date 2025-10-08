from smolagents import Tool

from evaluation.core.golden_dataset_manager import GoldenDatasetManager
from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)
from evaluation.golden_dataset_creation.setup import setup
from service.agent_core.data_management.columns import COL_COUNTRY
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path


def request_1_1_country_risk_information(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = (
        "Geben Sie mir die Risikoinformationen für jedes Land auf der "
        "Grundlage des maximalen Brutto-Risikos der einzelnen Rechtspositionen "
        "für die direkten Geschäftspartner (Brutto-Risiko T0). Summieren Sie alle "
        "Risikowerte je Land in einer neuen Spalte 'Gesamtrisiko' zusammen und "
        "sortieren Sie die endgültigen Daten nach dem Gesamtrisiko."
    )
    question_id = "risk_information_1_1_country_risk_information"

    # load data from brutto_file.parquet
    brutto_file = load_dataset_from_path(DATA_DIR / "brutto_file.parquet")
    country_col = COL_COUNTRY

    # create a new dataframe with the country and the T0 gross risk columns
    risk_columns = [col for col in brutto_file.columns if "Brutto-Risiko T0" in col]
    risk_analysis_data = brutto_file[[country_col] + risk_columns].copy()

    # aggregate risk_analysis_data for each country by max for each column
    risk_analysis_data_grouped = risk_analysis_data.groupby(country_col).max()

    # add total risk score and sort descending by total risk score
    risk_analysis_data_grouped["Gesamtrisiko"] = risk_analysis_data_grouped.sum(axis=1)
    risk_analysis_data_sorted = risk_analysis_data_grouped.sort_values(
        by="Gesamtrisiko", ascending=False
    )

    # Add to golden dataset
    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[risk_analysis_data_sorted],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=False,
        ),
    )


def create_country_risk_information_examples() -> None:
    manager, tools = setup()

    request_1_1_country_risk_information(manager, tools)
