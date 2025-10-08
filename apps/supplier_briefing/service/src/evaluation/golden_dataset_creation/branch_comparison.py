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
from service.agent_core.data_management.columns import COL_ESTELL_SEKTOR_DETAILLIERT_RAW
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path

golden_dataset_manager = GoldenDatasetManager()


def request_1_branch_comparison_unclear_branch(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    question = "Ich benötige einen Vergleich zwischen den Branchen Bau und Handwerk."
    question_id = "branch_comparison__request_1_branch_comparison_unclear_branch"

    # Generate ground truth answer
    possible_branches_list = [
        "F 01 CONSTRUCTION",
        "F 23 BEA 385 COMMERCIAL AND INDUSTRIAL MACHINERY AND EQUIPMENT REPAIR AND MAINTENANCE",
        "F 23 BEA 347 SERVICES TO BUILDINGS AND DWELLINGS",
        "F 23 BEA 384 ELECTRONIC AND PRECISION EQUIPMENT REPAIR AND MAINTENANCE",
    ]
    possible_branches = pd.Series(possible_branches_list)

    # Assemble expected output
    ground_truth_text = "Ich benötige weitere Informationen, um Ihre Anfrage zu beantworten. Ich habe mögliche Branchen zum Vergleich herausgesucht, die Ihrer Anfrage entsprechen. Wählen Sie zwei der aufgeführten Branchen aus."
    dataframes = [possible_branches]

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


def get_comparison_two_branches_averaged_per_country(
    branch_1: str, branch_2: str
) -> list[pd.DataFrame]:
    risk_per_branch = load_dataset_from_path(DATA_DIR / "risk_per_branch.parquet")
    branch_column = COL_ESTELL_SEKTOR_DETAILLIERT_RAW

    branch_1_risk_matrix = risk_per_branch.loc[(branch_1, "Brutto", "T0")]
    branch_2_risk_matrix = risk_per_branch.loc[(branch_2, "Brutto", "T0")]

    # Calculate mean across all rows (countries) - no need to drop columns if country is in index
    branch_1_aggregated = (
        branch_1_risk_matrix.mean(numeric_only=True).to_frame().T.round(2)
    )
    branch_2_aggregated = (
        branch_2_risk_matrix.mean(numeric_only=True).to_frame().T.round(2)
    )

    # Add branch identifier
    branch_1_aggregated[branch_column] = branch_1
    branch_2_aggregated[branch_column] = branch_2
    combined_dataframe = pd.concat(
        [branch_1_aggregated, branch_2_aggregated], ignore_index=True
    )

    combined_dataframe = combined_dataframe.set_index(branch_column)

    dataframes = [combined_dataframe]
    return dataframes


def request_1_2_branch_comparison_two_branches_averaged_per_country(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    branch_1 = "F 01 CONSTRUCTION"
    branch_2 = "F 23 BEA 385 COMMERCIAL AND INDUSTRIAL MACHINERY AND EQUIPMENT REPAIR AND MAINTENANCE"

    question = f'Ich benötige einen Vergleich zwischen den Brutto-Risiken der Branchen "{branch_1}" und "{branch_2}", wobei die Risikowerte über alle Länder hinweg gemittelt werden sollten.'
    question_id = (
        "branch_comparison__request_1_2_branch_comparison_two_branches_per_country"
    )

    dataframes = get_comparison_two_branches_averaged_per_country(branch_1, branch_2)

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=dataframes,  # type: ignore
        question_difficulty=QuestionDifficulty.EASY,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def request_2_1_branch_comparison_two_branches_for_specific_country(
    golden_dataset_manager: GoldenDatasetManager, tools: dict[str, Tool]
) -> None:
    branch_1 = "D 10 BEA 217 BREWERIES"
    branch_2 = "D 10 BEA 218 WINERIES"
    country = "BEL"

    branch_column = COL_ESTELL_SEKTOR_DETAILLIERT_RAW

    question = f'Ich benötige einen Vergleich zwischen den Brutto-Risiken der Branchen "{branch_1}" und "{branch_2}" für das Land Belgien.'
    question_id = "branch_comparison__request_2_1_branch_comparison_two_branches_for_specific_country"

    risk_per_branch = load_dataset_from_path(DATA_DIR / "risk_per_branch.parquet")

    # Extract branch risk martix
    branch_1_risk_matrix = risk_per_branch.loc[(branch_1, "Brutto", "T0")]
    branch_2_risk_matrix = risk_per_branch.loc[(branch_2, "Brutto", "T0")]

    branch_1_belgium = branch_1_risk_matrix.loc[branch_1_risk_matrix.index == country]
    branch_2_belgium = branch_2_risk_matrix.loc[branch_2_risk_matrix.index == country]

    # Add branch identifier
    branch_1_belgium = branch_1_belgium.copy()
    branch_2_belgium = branch_2_belgium.copy()

    branch_1_belgium[branch_column] = branch_1
    branch_2_belgium[branch_column] = branch_2

    # Combine both dataframes
    combined_belgium = pd.concat(
        [branch_1_belgium, branch_2_belgium], ignore_index=True
    )

    combined_belgium = combined_belgium.set_index(branch_column)

    dataframes = [combined_belgium]

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


def create_branch_comparison_examples() -> None:
    manager, tools = setup()

    request_1_branch_comparison_unclear_branch(manager, tools)
    request_1_2_branch_comparison_two_branches_averaged_per_country(manager, tools)
    request_2_1_branch_comparison_two_branches_for_specific_country(manager, tools)
