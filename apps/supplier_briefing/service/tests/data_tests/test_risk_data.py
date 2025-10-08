import pandas as pd
import pytest

from service.agent_core.constants import DATA_SOURCE_NHW
from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_ARTIKELFAMILIE,
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_UST_ID,
    COL_CONCRETE_RISK_T0_LEGAL_POSITIONS,
    COL_COUNTRY,
    COL_DATA_SOURCE,
    COL_ESTELL_SEKTOR_DETAILLIERT_RAW,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_ESTELL_SEKTOR_GROB_RAW,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_FINEST_PRODUCT_LEVEL,
    COL_FRUIT_VEG_GROUP,
    COL_GROSS_RISK_T0_LEGAL_POSITIONS,
    COL_GROSS_RISK_T1_LEGAL_POSITIONS,
    COL_GROSS_RISK_T1_N_LEGAL_POSITIONS,
    COL_GROSS_RISK_TN_LEGAL_POSITIONS,
    COL_GROUPING_FACHBEREICH,
    COL_HAUPTWARENGRUPPE,
    COL_ID_ARTICLE_NAME,
    COL_ID_ARTICLE_NAME_CONCRETE_FILE,
    COL_ID_ARTICLE_UNIQUE,
    COL_ID_ARTIKELFAMILIE,
    COL_ID_HAUPTWARENGRUPPE,
    COL_ID_UNTERWARENGRUPPE,
    COL_ID_WG_EBENE_3_WGI,
    COL_KONKRETE_PRIORISIERUNG,
    COL_NETTO_PRIORISIERUNG,
    COL_PRIORISIERUNGS_SCOPE,
    COL_PROCUREMENT_UNIT,
    COL_RELATIVE_PURCHASE_VALUE,
    COL_RESPONSIBLE_DEPARTMENT,
    COL_REVENUE_TOTAL,
    COL_RISIKOROHSTOFFE,
    COL_SCHWARZ_GROUP_FLAG,
    COL_SCHWARZBESCHAFFUNG,
    COL_UNTERWARENGRUPPE,
    COL_WG_EBENE_3_WGI,
    COL_WG_EBENE_7_KER_POSITION,
    COL_WG_EBENE_8_SACHKONTO,
    COL_WG_EBENE_9_KOSTENKATEGORIE,
    EMPTY_VALUES,
    HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS,
    NICHT_HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS,
)
from service.data_preparation import (
    COL_BUSINESS_PARTNER_NAME,
    assert_column_depends_on_other_column,
)
from tests.data_tests.utils import filter_for_non_empty_values

BUSINESS_PARTNERS_WITH_MULTIPLE_UST_IDS = ["21341433", "28000470"]


def test_business_partner_name_unique_for_business_partner_id(
    transactions_df: pd.DataFrame,
) -> None:
    assert_column_depends_on_other_column(transactions_df, COL_BUSINESS_PARTNER_NAME)


@pytest.mark.xfail(reason="likely fails due to pseudonymization errors")
def test_business_partner_name_unique_for_business_partner_id_in_brutto_df(
    brutto_df: pd.DataFrame,
) -> None:
    assert_column_depends_on_other_column(brutto_df, COL_BUSINESS_PARTNER_NAME)


def test_business_partner_name_unique_for_business_partner_id_in_concrete_df(
    concrete_df: pd.DataFrame,
) -> None:
    assert_column_depends_on_other_column(concrete_df, COL_BUSINESS_PARTNER_NAME)


def test_brutto_df_not_empty(brutto_df: pd.DataFrame) -> None:
    assert not brutto_df.empty


def test_concrete_df_not_empty(concrete_df: pd.DataFrame) -> None:
    assert not concrete_df.empty


def test_transactions_df_not_empty(transactions_df: pd.DataFrame) -> None:
    assert not transactions_df.empty


def test_brutto_df_datatypes_and_values(
    brutto_df: pd.DataFrame,
) -> None:
    assert brutto_df[COL_BUSINESS_PARTNER_ID].dtype == object
    assert brutto_df[COL_BUSINESS_PARTNER_NAME].dtype == object
    # Cannot convert to numeric:
    with pytest.raises(ValueError):
        brutto_df[COL_BUSINESS_PARTNER_ID].astype(int)
    # country codes are strings of length 3
    assert all(isinstance(country, str) for country in list(brutto_df[COL_COUNTRY]))
    assert set(brutto_df[COL_COUNTRY].apply(len)) == {3}
    assert set(brutto_df[COL_SCHWARZBESCHAFFUNG]) == {"nan", "x"}
    assert set(brutto_df[COL_SCHWARZ_GROUP_FLAG]) == {"N.A.", "X"}
    assert set(brutto_df[COL_REVENUE_TOTAL]) == {
        "1.000.000",
        "10.000.000",
        "100.000",
        "nan",
    }
    # assert_column_value_unique_for_business_partner_id(brutto_df.reset_index(drop=True), COL_REVENUE_TOTAL) # fails
    assert set(brutto_df[COL_RELATIVE_PURCHASE_VALUE]) == {
        "gering",
        "hoch",
        "mittel",
        "sehr hoch",
    }
    # assert_column_value_unique_for_business_partner_id(brutto_df.reset_index(drop=True), COL_RELATIVE_PURCHASE_VALUE) # fail
    assert set(brutto_df[COL_GROUPING_FACHBEREICH]) == {
        "Beschaffung",
        "EK B&P",
        "EK FOOD/NEAR FOOD",
        "EK NON FOOD",
        "EK O&G",
        "Immo",
        "Kunde",
        "Logistik",
        "Personal",
        "Unterstützungsprozesse",
    }
    assert brutto_df[COL_RESPONSIBLE_DEPARTMENT].dtype == object
    assert brutto_df[COL_ESTELL_SEKTOR_GROB_RAW].dtype == object
    assert brutto_df[COL_ESTELL_SEKTOR_DETAILLIERT_RAW].dtype == object
    # the values of COL_ESTELL_SEKTOR_GROB are not a subset of the values of COL_ESTELL_SEKTOR_DETAILLIERT
    assert not set(brutto_df[COL_ESTELL_SEKTOR_GROB_RAW]) <= set(
        brutto_df[COL_ESTELL_SEKTOR_DETAILLIERT_RAW]
    )
    assert set(brutto_df[COL_DATA_SOURCE]) == {
        "Datenerfassung Handelsware (HW)",
        "Datenerfassung Nicht-Handelsware (NHW)",
    }
    assert_column_depends_on_other_column(
        df=brutto_df,
        dependant_column=COL_BUSINESS_PARTNER_UST_ID,
        allowed_number_of_ids_multiple_values=2,
    )
    # exceptions
    assert (
        len(
            set(
                brutto_df[brutto_df[COL_BUSINESS_PARTNER_ID] == "28000470"][
                    COL_BUSINESS_PARTNER_UST_ID
                ]
            )
        )
        == 40
    )
    assert brutto_df[brutto_df[COL_BUSINESS_PARTNER_ID] == "28000470"].shape[0] == 540
    assert (
        len(
            set(
                brutto_df[brutto_df[COL_BUSINESS_PARTNER_ID] == "21341433"][
                    COL_BUSINESS_PARTNER_UST_ID
                ]
            )
        )
        == 2
    )
    assert brutto_df[brutto_df[COL_BUSINESS_PARTNER_ID] == "21341433"].shape[0] == 3

    assert set(brutto_df[COL_HAUPTWARENGRUPPE]) == {
        "BROT/BACK-/SÜSSWAREN/OTC",
        "BROT/BACK-/SÜßWAREN/OTC",
        "GEFLÜGEL/FLEISCH/FISCH",
        "GETRÄNKE",
        "KONSERVEN",
        "KÜHLUNG",
        "NAHRUNGSMITTEL",
        "NON FOOD",
        "NON-FOOD-SORTIMENT",
        "OBST & GEMÜSE, BLUMEN",
        "TIKO",
        "nan",
    }
    assert set(brutto_df[COL_WG_EBENE_3_WGI]) == {
        "30 GEFLÜGEL/FLEISCH",
        "32 FRISCHFISCH",
        "40 TIKO",
        "50 KÜHLUNG",
        "60 FOOD TS",
        "90 FRISCHBROT / HOT CONVENIENCE",
        "BLUMEN (B+P)",
        "N.A.",
        "NON FOOD (AKT)",
        "OBST & GEMÜSE (O+G)",
    }

    assert_column_depends_on_other_column(
        brutto_df,
        dependant_column=COL_WG_EBENE_3_WGI,
        independent_columns=[COL_ID_WG_EBENE_3_WGI],
    )
    assert_column_depends_on_other_column(
        brutto_df,
        dependant_column=COL_UNTERWARENGRUPPE,
        independent_columns=[COL_ID_UNTERWARENGRUPPE],
    )
    assert_column_depends_on_other_column(
        brutto_df,
        dependant_column=COL_FINEST_PRODUCT_LEVEL,
        independent_columns=[COL_ARTICLE_NAME],
        allowed_number_of_ids_multiple_values=1,
    )
    assert_column_depends_on_other_column(
        brutto_df,
        dependant_column=COL_ARTICLE_NAME,
        independent_columns=[COL_FINEST_PRODUCT_LEVEL],
        allowed_number_of_ids_multiple_values=2,
    )

    # assert_column_depends_on_other_column(brutto_df, dependant_column=COL_ARTIKELFAMILIE, independent_column=COL_ID_ARTIKELFAMILIE) # fails
    # assert_column_depends_on_other_column(brutto_df, dependant_column=COL_FRUIT_VEG_GROUP, independent_column=COL_ID_FRUIT_VEG_GROUP) # fails


def test_risikorohstoffe_column_depends_on_other_columns_in_brutto_df(
    brutto_df: pd.DataFrame,
) -> None:
    assert_column_depends_on_other_column(
        brutto_df,
        dependant_column=COL_RISIKOROHSTOFFE,
        independent_columns=[
            COL_BUSINESS_PARTNER_ID,
            COL_UNTERWARENGRUPPE,
            COL_ARTIKELFAMILIE,
            COL_FINEST_PRODUCT_LEVEL,
            COL_WG_EBENE_7_KER_POSITION,
            COL_WG_EBENE_8_SACHKONTO,
            COL_WG_EBENE_9_KOSTENKATEGORIE,
        ],
        allowed_number_of_ids_multiple_values=1,
    )


def test_brutto_df_contains_gross_risk_legal_position_columns(
    brutto_df: pd.DataFrame,
) -> None:
    for col in (
        COL_GROSS_RISK_T0_LEGAL_POSITIONS
        + COL_GROSS_RISK_T1_LEGAL_POSITIONS
        + COL_GROSS_RISK_TN_LEGAL_POSITIONS
        + COL_GROSS_RISK_T1_N_LEGAL_POSITIONS
    ):
        assert col in list(brutto_df.columns)


def test_brutto_df_and_brutto_df_cleaned(
    brutto_df: pd.DataFrame, brutto_df_cleaned: pd.DataFrame
) -> None:
    # one column (Ust.-ID) was dropped in the cleaning process
    assert brutto_df_cleaned.shape[1] == brutto_df.shape[1] - 1
    assert set(brutto_df[COL_BUSINESS_PARTNER_ID]) == set(
        brutto_df_cleaned[COL_BUSINESS_PARTNER_ID]
    )


def test_priority_scope_column_in_brutto_and_concrete(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame
) -> None:
    assert COL_PRIORISIERUNGS_SCOPE in brutto_df.columns
    assert COL_PRIORISIERUNGS_SCOPE in concrete_df.columns


@pytest.mark.parametrize(
    "business_partner_id_with_multiple_ust_ids",
    BUSINESS_PARTNERS_WITH_MULTIPLE_UST_IDS,
)
def test_brutto_df_duplicates_with_multiple_ust_ids_are_only_nhw(
    brutto_df: pd.DataFrame, business_partner_id_with_multiple_ust_ids: str
) -> None:
    brutto_df_filtered = brutto_df[
        brutto_df[COL_BUSINESS_PARTNER_ID] == business_partner_id_with_multiple_ust_ids
    ]

    assert brutto_df_filtered[COL_DATA_SOURCE].eq(DATA_SOURCE_NHW).all()


@pytest.mark.parametrize(
    "column",
    [
        COL_BUSINESS_PARTNER_NAME,
        COL_COUNTRY,
        COL_SCHWARZBESCHAFFUNG,
        COL_SCHWARZ_GROUP_FLAG,
        COL_REVENUE_TOTAL,
        COL_RELATIVE_PURCHASE_VALUE,
        COL_GROUPING_FACHBEREICH,
        COL_ESTELL_SEKTOR_DETAILLIERT_RAW,
    ],
)
def test_compare_brutto_df_and_concrete_df_column_has_same_values(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame, column: str
) -> None:
    assert set(brutto_df[column]) == set(concrete_df[column])


@pytest.mark.parametrize(
    "column",
    [
        COL_DATA_SOURCE,
        COL_ESTELL_SEKTOR_DETAILLIERT_RAW,
        COL_FRUIT_VEG_GROUP,
        COL_GROUPING_FACHBEREICH,
        COL_ID_HAUPTWARENGRUPPE,
        COL_ID_UNTERWARENGRUPPE,
        COL_PROCUREMENT_UNIT,
        COL_RELATIVE_PURCHASE_VALUE,
        COL_REVENUE_TOTAL,
        COL_SCHWARZ_GROUP_FLAG,
        COL_SCHWARZBESCHAFFUNG,
        COL_UNTERWARENGRUPPE,
    ],
)
def test_compare_brutto_df_values_contained_in_concrete_df_values_for_column(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame, column: str
) -> None:
    assert set(brutto_df[column]) <= set(concrete_df[column])


@pytest.mark.parametrize(
    "column",
    [
        COL_BUSINESS_PARTNER_ID,
        COL_COUNTRY,
        COL_DATA_SOURCE,
        COL_ESTELL_SEKTOR_DETAILLIERT_RAW,
        COL_FRUIT_VEG_GROUP,
        COL_GROUPING_FACHBEREICH,
        COL_ID_ARTIKELFAMILIE,
        COL_ID_HAUPTWARENGRUPPE,
        COL_PROCUREMENT_UNIT,
        COL_RELATIVE_PURCHASE_VALUE,
        COL_REVENUE_TOTAL,
        COL_SCHWARZ_GROUP_FLAG,
        COL_SCHWARZBESCHAFFUNG,
    ],
)
def test_compare_concrete_df_values_contained_in_brutto_df_values_for_column(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame, column: str
) -> None:
    assert set(concrete_df[column]) <= set(brutto_df[column])


def test_concrete_df_datatypes_and_values(
    concrete_df: pd.DataFrame,
) -> None:
    assert concrete_df[COL_BUSINESS_PARTNER_ID].dtype == object
    assert concrete_df[COL_BUSINESS_PARTNER_NAME].dtype == object
    # Cannot convert to numeric:
    with pytest.raises(ValueError):
        concrete_df[COL_BUSINESS_PARTNER_ID].astype(int)
    # country codes are strings of length 3
    assert all(isinstance(country, str) for country in list(concrete_df[COL_COUNTRY]))
    assert set(concrete_df[COL_COUNTRY].apply(len)) == {3}
    assert set(concrete_df[COL_SCHWARZBESCHAFFUNG]) == {"nan", "x"}
    assert set(concrete_df[COL_SCHWARZ_GROUP_FLAG]) == {"N.A.", "X"}
    assert set(concrete_df[COL_REVENUE_TOTAL]) == {
        "1.000.000",
        "10.000.000",
        "100.000",
        "nan",
    }
    # assert_column_value_unique_for_business_partner_id(brutto_df.reset_index(drop=True), COL_REVENUE_TOTAL) # fails
    assert set(concrete_df[COL_RELATIVE_PURCHASE_VALUE]) == {
        "gering",
        "hoch",
        "mittel",
        "sehr hoch",
    }
    # assert_column_value_unique_for_business_partner_id(brutto_df.reset_index(drop=True), COL_RELATIVE_PURCHASE_VALUE) # fail
    assert set(concrete_df[COL_GROUPING_FACHBEREICH]) == {
        "Beschaffung",
        "EK B&P",
        "EK FOOD/NEAR FOOD",
        "EK NON FOOD",
        "EK O&G",
        "Immo",
        "Kunde",
        "Logistik",
        "Personal",
        "Unterstützungsprozesse",
    }
    assert concrete_df[COL_RESPONSIBLE_DEPARTMENT].dtype == object
    assert concrete_df[COL_ESTELL_SEKTOR_GROB_RAW].dtype == object
    assert concrete_df[COL_ESTELL_SEKTOR_DETAILLIERT_RAW].dtype == object
    # the values of COL_ESTELL_SEKTOR_GROB are not a subset of the values of COL_ESTELL_SEKTOR_DETAILLIERT
    assert not set(concrete_df[COL_ESTELL_SEKTOR_GROB_RAW]) <= set(
        concrete_df[COL_ESTELL_SEKTOR_DETAILLIERT_RAW]
    )
    assert set(concrete_df[COL_DATA_SOURCE]) == {
        "Datenerfassung Handelsware (HW)",
        "Datenerfassung Nicht-Handelsware (NHW)",
    }
    assert set(concrete_df[COL_HAUPTWARENGRUPPE]) == {
        "OBST & GEMÜSE, BLUMEN",
        "KONSERVEN",
        "N.A.",
        "BROT/BACK-/SÜSSWAREN/OTC",
        "KÜHLUNG",
        "NON FOOD",
        "GETRÄNKE",
        "NAHRUNGSMITTEL",
    }
    assert set(concrete_df[COL_WG_EBENE_3_WGI]) == {
        "30 GEFLÜGEL/FLEISCH",
        "40 TIKO",
        "32 FRISCHFISCH",
        "NON FOOD (AKT)",
        "BLUMEN (B+P)",
        "nan",
        "50 KÜHLUNG",
        "60 FOOD TS",
        "90 FRISCHBROT / HOT CONVENIENCE",
        "OBST & GEMÜSE (O+G)",
    }

    assert_column_depends_on_other_column(
        concrete_df,
        dependant_column=COL_WG_EBENE_3_WGI,
        independent_columns=[COL_ID_WG_EBENE_3_WGI],
    )
    assert_column_depends_on_other_column(
        concrete_df,
        dependant_column=COL_UNTERWARENGRUPPE,
        independent_columns=[COL_ID_UNTERWARENGRUPPE],
    )
    # assert_column_depends_on_other_column(concrete_df, dependant_column=COL_ARTIKELFAMILIE, independent_column=COL_ID_ARTIKELFAMILIE) # fails
    # assert_column_depends_on_other_column(concrete_df, dependant_column=COL_FRUIT_VEG_GROUP, independent_column=COL_ID_FRUIT_VEG_GROUP) # fails
    assert_column_depends_on_other_column(
        concrete_df,
        dependant_column=COL_ARTICLE_NAME,
        independent_columns=[COL_ID_ARTICLE_UNIQUE],
    )


@pytest.mark.xfail(
    reason="Fails due to inconsistent handling of empty values, see TBAF-317"
)
def test_business_partners_df_datatypes_and_values(
    business_partners_df: pd.DataFrame,
) -> None:
    assert_column_depends_on_other_column(
        business_partners_df.reset_index(drop=True), COL_BUSINESS_PARTNER_NAME
    )
    assert business_partners_df[COL_BUSINESS_PARTNER_ID].dtype == object
    assert business_partners_df[COL_BUSINESS_PARTNER_NAME].dtype == object
    with pytest.raises(ValueError):
        business_partners_df[COL_BUSINESS_PARTNER_ID].astype(int)
    # country codes are strings of length 3
    assert all(
        isinstance(country, str) for country in list(business_partners_df[COL_COUNTRY])
    )
    assert set(business_partners_df[COL_COUNTRY].apply(len)) == {3}
    assert set(business_partners_df[COL_SCHWARZBESCHAFFUNG]) == {"nan", "x"}
    assert set(business_partners_df[COL_SCHWARZ_GROUP_FLAG]) == {"N.A.", "X"}
    assert_column_depends_on_other_column(
        business_partners_df.reset_index(drop=True), COL_REVENUE_TOTAL
    )

    # assert set(business_partners_df[COL_REVENUE_TOTAL]) == {'1.000.000', '10.000.000', '100.000', 'nan'}
    # assert set(business_partners_df[COL_RELATIVE_PURCHASE_VALUE]) == {'gering', 'hoch', 'mittel', 'sehr hoch'}
    # assert set(business_partners_df[COL_GROUPING_FACHBEREICH]) == {'Beschaffung', 'EK B&P', 'EK FOOD/NEAR FOOD', 'EK NON FOOD', 'EK O&G', 'Immo', 'Kunde', 'Logistik', 'Personal', 'Unterstützungsprozesse'}
    assert business_partners_df[COL_RESPONSIBLE_DEPARTMENT].dtype == object
    assert business_partners_df[COL_ESTELL_SEKTOR_GROB_RENAMED].dtype == object
    assert business_partners_df[COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED].dtype == object
    # the values of COL_ESTELL_SEKTOR_GROB are not a subset of the values of COL_ESTELL_SEKTOR_DETAILLIERT
    assert not set(business_partners_df[COL_ESTELL_SEKTOR_GROB_RENAMED]) <= set(
        business_partners_df[COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED]
    )
    assert set(business_partners_df[COL_NETTO_PRIORISIERUNG]) == {
        "",
        "1",
        "2",
        "3",
        "4",
        "5",
    }
    assert set(business_partners_df[COL_KONKRETE_PRIORISIERUNG]) == {
        "",
        "1",
        "2",
        "3",
        "4",
        "5",
    }
    assert COL_ESTELL_SEKTOR_GROB_RENAMED in business_partners_df.columns
    assert COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED in business_partners_df.columns


def test_concrete_article_name_number_values_contained_in_brutto(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame
) -> None:
    """
    Ensure all values from the article name number column in brutto_df are
    present in concrete_df as well.
    """
    brutto_values = set(filter_for_non_empty_values(brutto_df[COL_ID_ARTICLE_NAME]))
    concrete_values = set(
        filter_for_non_empty_values(concrete_df[COL_ID_ARTICLE_NAME_CONCRETE_FILE])
    )

    missing_in_brutto = concrete_values - brutto_values
    print(
        f"Values in concrete but not in brutto (count: {len(missing_in_brutto)}): {missing_in_brutto}"
    )

    assert concrete_values <= brutto_values


def test_concrete_article_name_contained_in_brutto_finest_product_level(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame
) -> None:
    """
    Ensure that the article names in the concrete dataset are contained in the finest
    product level entries in the brutto dataset.
    """
    concrete_set = set(
        concrete_df[COL_ARTICLE_NAME][
            ~concrete_df[COL_ARTICLE_NAME].isin(EMPTY_VALUES)
        ].dropna()
    )
    brutto_set = set(
        brutto_df[COL_FINEST_PRODUCT_LEVEL][
            ~brutto_df[COL_FINEST_PRODUCT_LEVEL].isin(EMPTY_VALUES)
        ].dropna()
    )

    missing_in_brutto = concrete_set - brutto_set
    print(
        f"Values in concrete but not in brutto (count: {len(missing_in_brutto)}): {missing_in_brutto}"
    )

    assert concrete_set <= brutto_set


def test_transactions_df_columns(transactions_df: pd.DataFrame) -> None:
    assert COL_ESTELL_SEKTOR_GROB_RENAMED in transactions_df.columns
    assert COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED in transactions_df.columns
    assert COL_ESTELL_SEKTOR_GROB_RAW not in transactions_df.columns
    assert COL_ESTELL_SEKTOR_DETAILLIERT_RAW not in transactions_df.columns
    assert COL_ID_ARTICLE_NAME_CONCRETE_FILE not in transactions_df.columns
    assert COL_ID_ARTICLE_NAME in transactions_df.columns


def test_transactions_pseudo_primary_key(transactions_df: pd.DataFrame) -> None:
    pseudo_pk_columns = list(
        set(
            HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS
            + NICHT_HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS
        )
    )
    grouped = transactions_df.groupby(pseudo_pk_columns).size()
    duplicates = grouped[grouped > 1]
    assert duplicates.shape[0] <= 155, (
        f"More duplicates found than expected for pseudo primary key columns: {pseudo_pk_columns}"
    )


def test_transactions_df_number_of_rows_approx(
    transactions_df: pd.DataFrame,
    brutto_df_cleaned: pd.DataFrame,
    concrete_df_cleaned: pd.DataFrame,
) -> None:
    assert transactions_df.shape[0] == pytest.approx(446233, rel=0.01)


def test_almost_all_transaction_entries_contains_data_from_brutto_and_concrete_file(
    transactions_df: pd.DataFrame,
) -> None:
    COL_CONCRETE_RISK_PRESENT = "concrete_risk_present"
    COL_BRUTTO_RISK_PRESENT = "brutto_risk_present"

    concrete_risk_mask = transactions_df[
        COL_CONCRETE_RISK_T0_LEGAL_POSITIONS
    ].notna() & ~transactions_df[COL_CONCRETE_RISK_T0_LEGAL_POSITIONS].isin(
        EMPTY_VALUES
    )
    transactions_df = transactions_df.copy()
    transactions_df[COL_CONCRETE_RISK_PRESENT] = concrete_risk_mask.any(axis=1)

    brutto_risk_mask = transactions_df[
        COL_GROSS_RISK_T0_LEGAL_POSITIONS
    ].notna() & ~transactions_df[COL_GROSS_RISK_T0_LEGAL_POSITIONS].isin(EMPTY_VALUES)
    transactions_df[COL_BRUTTO_RISK_PRESENT] = brutto_risk_mask.any(axis=1)

    PSEUDO_PRIMARY_KEY_COLUMNS: tuple[str, ...] = tuple(
        dict.fromkeys(
            (
                *HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS,
                *NICHT_HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS,
            )
        )
    )

    # Group and check if any row in each group has data
    grouped_by_pseudo_priamry_key_columns = transactions_df.groupby(
        [*PSEUDO_PRIMARY_KEY_COLUMNS]
    ).agg({COL_CONCRETE_RISK_PRESENT: "any", COL_BRUTTO_RISK_PRESENT: "any"})

    total_groups = len(grouped_by_pseudo_priamry_key_columns)
    brutto_risk_percentage = (
        grouped_by_pseudo_priamry_key_columns[COL_BRUTTO_RISK_PRESENT].sum()
        / total_groups
    ) * 100
    concrete_risk_percentage = (
        grouped_by_pseudo_priamry_key_columns[COL_CONCRETE_RISK_PRESENT].sum()
        / total_groups
    ) * 100

    both_risk_categories_present = (
        grouped_by_pseudo_priamry_key_columns[COL_BRUTTO_RISK_PRESENT]
        & grouped_by_pseudo_priamry_key_columns[COL_CONCRETE_RISK_PRESENT]
    )
    both_risk_categories_present_percentage = (
        both_risk_categories_present.sum() / total_groups
    ) * 100

    assert brutto_risk_percentage >= 99.5, (
        f"Only {brutto_risk_percentage:.2f}% of groups have brutto risk data"
    )
    assert concrete_risk_percentage >= 99.99, (
        f"Only {concrete_risk_percentage:.2f}% of groups have concrete risk data"
    )
    assert both_risk_categories_present_percentage >= 99.5, (
        f"Only {both_risk_categories_present_percentage:.2f}% of groups have both brutto and concrete risk data. "
    )
