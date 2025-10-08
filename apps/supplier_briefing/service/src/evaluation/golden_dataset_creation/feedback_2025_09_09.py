from evaluation.core.golden_dataset_manager import GoldenDatasetManager
from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)
from evaluation.golden_dataset_creation.setup import setup
from service.agent_core.data_management.columns import (
    COL_COUNTRY,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
)
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path


def countries_of_business_partners_in_construction(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = (
        "In welchen Ländern haben wir GP, die in der Branche Construction tätig sind?"
    )
    question_id = "feedback_2025_09_08_countries_of_business_partners_in_construction"

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text="Die Branche ist nicht eindeutig definiert. Bitte spezifizieren Sie, ob Sie den 'estell Sektor grob' oder 'estell Sektor detailliert' meinen.",
        pandas_objects=[],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def countries_of_business_partners_in_construction_estell_grob(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = "In welchen Ländern haben wir GP, die in der Branche (estell Sektor grob) Construction tätig sind?"
    question_id = (
        "feedback_2025_09_08_countries_of_business_partners_in_construction_estell_grob"
    )

    transcations_df = load_dataset_from_path(DATA_DIR / "transactions.parquet")
    transactions_in_constructions = transcations_df[
        transcations_df[COL_ESTELL_SEKTOR_GROB_RENAMED] == "F 01 CONSTRUCTION"
    ]
    transactions_in_constructions_countries = (
        transactions_in_constructions[COL_COUNTRY]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[transactions_in_constructions_countries],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=True,
            ignore_column_names=True,
        ),
    )


def create_feedback_2025_09_08_examples() -> None:
    manager, _ = setup()

    countries_of_business_partners_in_construction(manager)
    countries_of_business_partners_in_construction_estell_grob(manager)


if __name__ == "__main__":
    create_feedback_2025_09_08_examples()
