import pandas as pd

from evaluation.core.golden_dataset_manager import GoldenDatasetManager
from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)
from evaluation.golden_dataset_creation.setup import setup
from service.agent_core.constants import DATA_SOURCE_NHW
from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_CONCRETE_RISK_T0_LEGAL_POSITIONS,
    COL_COUNTRY,
    COL_DATA_SOURCE,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_GROUPING_FACHBEREICH,
    COL_PART_OF_SCHWARZ,
    COL_RISIKOROHSTOFFE,
)
from service.agent_core.data_management.transactions import Transactions
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path
from service.data_preparation import BUSINESS_PARTNERS_PARQUET


def request_2_assigned_resources_to_business_partners_in_branch(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = "Welche Rohstoffe wurden Geschäftspartnern im Fachbereich Obst und Gemüse zugeordnet?"
    question_id = "feedback_2025_08_28_request_2_assigned_resources_to_business_partners_in_branch"

    transactions_df = Transactions.df()

    transactions_filtered = transactions_df[
        transactions_df[COL_GROUPING_FACHBEREICH] == "EK O&G"
    ]
    og_resources = transactions_filtered[COL_RISIKOROHSTOFFE].dropna().unique()

    og_resources_series = pd.Series(og_resources, name=COL_RISIKOROHSTOFFE)

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[og_resources_series],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=True,
            ignore_column_names=True,
        ),
    )


def request_3_na_risk_resources_in_og_department(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = "Welche Produkte aus dem Fachbereich Obst und Gemüse haben keine Rohstoffe zugeordnet?"
    question_id = "feedback_2025_08_28_request_3_na_risk_resources_in_og_department"

    transactions_df = Transactions.df()

    transactions_filtered = transactions_df[
        transactions_df[COL_GROUPING_FACHBEREICH] == "EK O&G"
    ]
    na_resource_products = transactions_filtered[
        (transactions_filtered[COL_RISIKOROHSTOFFE] == "N.A.")
        | (transactions_filtered[COL_RISIKOROHSTOFFE].isna())
    ][
        COL_ARTICLE_NAME
    ].unique()  # COL_ARTIKELFAMILIE would also be ok according to customer

    output_df = pd.DataFrame(na_resource_products, columns=[COL_ARTICLE_NAME])
    output_df = output_df.reset_index(drop=True)

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[output_df],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=True,
            ignore_column_names=True,
        ),
    )


def request_4_country_filtered_business_partners(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = "Bitte gebe mir eine Liste der Geschäftspartner mit Sitz in Österreich. In der Ausgabe reichen der Name und das Land als Spalten."
    question_id = "feedback_2025_08_28_request_4_country_filtered_business_partners"

    output_cols = [
        COL_BUSINESS_PARTNER_NAME,
        COL_COUNTRY,
    ]

    transactions_df = Transactions.df()
    bp_df = load_dataset_from_path(DATA_DIR / BUSINESS_PARTNERS_PARQUET)

    transactions_df_filtered = transactions_df[transactions_df[COL_COUNTRY] == "AUT"]
    austria_ids = transactions_df_filtered[COL_BUSINESS_PARTNER_ID].unique()

    bp_df_filtered = bp_df.loc[austria_ids]
    output_df = bp_df_filtered[output_cols]

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[output_df],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=True,
        ),
    )


def request_6_part_of_schwarz(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = "Bitte gebe mir eine Liste mit den Unternehmen, welche zur Schwarzgruppe gehören. In der Ausgabe reichen der Name und die Zugehörigkeit zur Schwarzgruppe als Spalten."
    question_id = "feedback_2025_08_28_request_6_part_of_schwarz"

    output_cols = [
        COL_BUSINESS_PARTNER_NAME,
        COL_PART_OF_SCHWARZ,
    ]

    bp_df = load_dataset_from_path(DATA_DIR / BUSINESS_PARTNERS_PARQUET)

    df_filtered = bp_df[bp_df[COL_PART_OF_SCHWARZ] == "X"]
    assert isinstance(df_filtered, pd.DataFrame)

    output_df = df_filtered[output_cols]
    assert isinstance(df_filtered, pd.DataFrame)

    golden_dataset_manager.add_entry(
        research_question=question,
        question_id=question_id,
        ground_truth_text=None,
        pandas_objects=[output_df],
        pandas_comparison_config=PandasComparisonConfig(
            mode=PandasComparisonMode.SORT_AND_EXACT_MATCH,
            drop_index=True,
        ),
    )


def request_7_legal_position_ranking_nhw_analysis(
    golden_dataset_manager: GoldenDatasetManager,
) -> None:
    question = """Ich möchte gerne die priorisierten Risiken im Bereich der Nicht-Handelsware (NHW) ermitteln. 
- Bitte aggregiere hierfür auf Ebene der Estell-Sektoren je Geschäftspartner die einzelnen Risiken nach dem Maximalprinzip je Rechtsposition 
- Summiere danach die aggregierten Werte über alle betroffenen Geschäftspartner 
- Bilde einen Rang je Rechtsposition (absteigend nach dem ermittelten Summenwert)
"""
    question_id = "feedback_2025_08_28_request_7_legal_position_ranking_nhw_analysis"

    # Load the dataset
    df = Transactions.df()

    # Step 1: Filter for NHW (Nicht-Handelsware)
    df_nhw = df[df[COL_DATA_SOURCE] == DATA_SOURCE_NHW].copy()

    # Step 2: Aggregate by Estelle-Sektor per GP using Maximum Principle
    # Group by GP_ID and Estelle-Sektor, then take max of each legal position

    df_max_per_sektor = (
        df_nhw.groupby(
            [COL_BUSINESS_PARTNER_ID, COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED]
        )[COL_CONCRETE_RISK_T0_LEGAL_POSITIONS]
        .max()
        .reset_index()
    )

    # Step 3: Sum across all business partners per legal position
    # Sum all the max values for each legal position
    sums = df_max_per_sektor[COL_CONCRETE_RISK_T0_LEGAL_POSITIONS].sum()

    # Step 4: Create ranking (descending by sum)
    output_col_rank = "Rang"
    output_col_rechtsposition = "Rechtsposition"
    output_col_sum = "Summe"
    result_df = pd.DataFrame(
        {output_col_rechtsposition: sums.index, output_col_sum: sums.values}
    )

    # Sort by sum descending and add rank
    result_df = result_df.sort_values(output_col_sum, ascending=False).reset_index(
        drop=True
    )
    result_df[output_col_rank] = (
        result_df[output_col_sum].rank(method="min", ascending=False).astype(int)
    )

    # Reorder columns to match expected output
    result_df = result_df[[output_col_rank, output_col_sum, output_col_rechtsposition]]

    dataframes = [result_df]

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


def create_feedback_2025_08_28_examples() -> None:
    manager, _ = setup()

    request_2_assigned_resources_to_business_partners_in_branch(manager)
    request_3_na_risk_resources_in_og_department(manager)
    request_4_country_filtered_business_partners(manager)
    request_6_part_of_schwarz(manager)
    request_7_legal_position_ranking_nhw_analysis(manager)


if __name__ == "__main__":
    create_feedback_2025_08_28_examples()
