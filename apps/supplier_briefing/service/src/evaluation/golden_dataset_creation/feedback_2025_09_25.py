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
    COL_ARTICLE_NAME,
    COL_COUNTRY,
    COL_FRUIT_VEG_GROUP,
    COL_GROSS_RISK_T0_LEGAL_POSITIONS,
    COL_RISKIEST_RESOURCE_KONKRET,
)
from service.agent_core.data_management.transactions import Transactions


def hannah_request_1_source_countries_for_dates(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = "Aus welchen Ländern bekommen wir Datteln?"
    question_id = "feedback_2025_09_25_hannah_request_1_source_countries_for_dates"

    transactions_df = Transactions.df()

    datteln_df = transactions_df[transactions_df[COL_FRUIT_VEG_GROUP] == "DATTELN"]
    countries = datteln_df[COL_COUNTRY].drop_duplicates()

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[countries],
        question_difficulty=QuestionDifficulty.HARD,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            ignore_column_names=True,
        ),
    )


def hannah_request_2_riskiest_resources_from_turkey(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = "Was sind die risikoreichsten Rohstoffe (konkret), die unseren Geschäftspartnern in der Türkei zugeordnet sind?"
    question_id = "feedback_2025_09_25_hannah_request_2_riskiest_resources_from_turkey"

    transactions_df = Transactions.df()

    turkey_partners_df = transactions_df[transactions_df[COL_COUNTRY] == "TUR"]
    riskiest_raw_materials = turkey_partners_df[
        COL_RISKIEST_RESOURCE_KONKRET
    ].value_counts()

    # Remove 'nan' values as they are not informative (were not properly cleaned before)
    riskiest_raw_materials_cleaned = riskiest_raw_materials.drop(
        ["nan"], errors="ignore"
    )

    ground_truth_text = "Die Häufigkeiten der risikoreichsten Rohstoffe, die mit unseren Geschäftspartnern mit Sitz in der Türkei in Verbindung gebracht werden, finden Sie folgender Tabelle."

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=ground_truth_text,
        pandas_objects=[riskiest_raw_materials_cleaned],
        question_difficulty=QuestionDifficulty.HARD,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
        ),
    )


def alexander_request_1_country_with_highest_risk_for_blueberries(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = "In welchem Land haben HEIDELBEEREN (Produkte) das größte Risiko?"
    question_id = "feedback_2025_09_25_alexander_request_1_country_with_highest_risk_for_blueberries"
    transactions_df = Transactions.df()
    blueberries_df = transactions_df[
        transactions_df[COL_ARTICLE_NAME].str.contains(
            "HEIDELBEEREN", case=False, na=False
        )
    ]
    # TODO: blueberries_df contains also articles that are not pure blueberries, e.g.'YOPRO SPOONABLE JOGHURT, HEIDELBEEREN', '"AURUM" VANILLEEIS MIT HEIDELBEEREN'. Decide how to deal with this.
    blueberries_df_group_by_country = blueberries_df.groupby([COL_COUNTRY])[
        COL_GROSS_RISK_T0_LEGAL_POSITIONS
    ]
    sums = blueberries_df_group_by_country.sum()
    sum_column = "Brutto-Risiko T0 (unmittelbarer Geschäftspartner) - Summe aller Rechtspositionen"
    sums[sum_column] = sums.sum(axis=1)
    sums.sort_values(by=sum_column, ascending=False, inplace=True)
    ground_truth_text = "Folgende Tabelle zeigt die Länder mit dem höchsten Risiko für Produkte, deren Artikelbezeichnung 'Heidelbeeren' enthält, sortiert nach dem Brutto-Risiko T0 (unmittelbarer Geschäftspartner) summiert über alle Rechtspositionen."

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=ground_truth_text,
        pandas_objects=[sums],
        question_difficulty=QuestionDifficulty.HARD,
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH,
        ),
    )


def create_feedback_2025_09_25_examples() -> None:
    manager, _ = setup()
    alexander_request_1_country_with_highest_risk_for_blueberries(manager)
    hannah_request_1_source_countries_for_dates(manager)
    hannah_request_2_riskiest_resources_from_turkey(manager)


if __name__ == "__main__":
    create_feedback_2025_09_25_examples()
