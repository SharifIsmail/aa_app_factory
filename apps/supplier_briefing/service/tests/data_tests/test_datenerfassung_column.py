from enum import StrEnum

import pandas as pd
import pytest
from _pytest.fixtures import FixtureRequest

from service.agent_core.constants import DATA_SOURCE_HW, DATA_SOURCE_NHW
from service.agent_core.data_management.columns import (
    COL_ABWICKLUNGSART,
    COL_ARTICLE_NAME,
    COL_ARTIKELFAMILIE,
    COL_BUSINESS_PARTNER_UST_ID,
    COL_DATA_SOURCE,
    COL_FRUIT_VEG_GROUP,
    COL_HAUPTWARENGRUPPE,
    COL_ID_ARTIKELFAMILIE,
    COL_ID_FRUIT_VEG_GROUP,
    COL_ID_HAUPTWARENGRUPPE,
    COL_ID_UNTERWARENGRUPPE,
    COL_ID_WG_EBENE_3_WGI,
    COL_ID_WG_EBENE_7_KER_POSITION,
    COL_ID_WG_EBENE_8_SACHKONTO,
    COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
    COL_MARKENTYP_HANDELSWARE,
    COL_PLACE_OF_PRODUCTION_COUNTRY,
    COL_PLACE_OF_PRODUCTION_ID,
    COL_PLACE_OF_PRODUCTION_NAME,
    COL_UNTERWARENGRUPPE,
    COL_WG_EBENE_3_WGI,
    COL_WG_EBENE_7_KER_POSITION,
    COL_WG_EBENE_8_SACHKONTO,
    COL_WG_EBENE_9_KOSTENKATEGORIE,
    EMPTY_VALUES,
)
from service.data_preparation import assert_split_into_two_distinct_data_sources
from tests.data_tests.utils import filter_for_non_empty_values

##############################################################
### Tests across both Datenerfassung values
##############################################################


class DataSource(StrEnum):
    data_source_hw = DATA_SOURCE_HW
    data_source_nhw = DATA_SOURCE_NHW


@pytest.mark.parametrize("data_source", [DATA_SOURCE_HW, DATA_SOURCE_NHW])
def test_article_name_not_always_empty_for_concrete_df(
    concrete_df: pd.DataFrame, data_source: DataSource
) -> None:
    subset = concrete_df[concrete_df[COL_DATA_SOURCE] == data_source]
    if subset.empty:
        return

    non_empty_names = filter_for_non_empty_values(
        subset[COL_ARTICLE_NAME].astype(str).str.strip()
    )
    assert not non_empty_names.empty


@pytest.mark.parametrize(
    "df_fixture_name",
    [
        "brutto_df",
        "concrete_df",
        "brutto_df_cleaned",
        "concrete_df_cleaned",
    ],
)
def test_dataframe_split_into_expected_data_sources(
    df_fixture_name: str, request: FixtureRequest
) -> None:
    df: pd.DataFrame = request.getfixturevalue(df_fixture_name)
    assert_split_into_two_distinct_data_sources(df)


##############################################################
### Tests for Datenerfassung: Nicht-Handelsware
##############################################################
def assert_columns_empty_for_data_source(
    df: pd.DataFrame,
    data_source: DataSource,
    columns_to_check: list[str],
) -> None:
    """Helper function to assert that specified columns are empty for a given data source."""
    filtered_df = df[df[COL_DATA_SOURCE] == data_source]
    if filtered_df.empty:
        return
    for col in columns_to_check:
        empty_values = list(EMPTY_VALUES)
        if col is COL_PLACE_OF_PRODUCTION_NAME:
            empty_values.extend("0")

        non_empty = filter_for_non_empty_values(
            filtered_df[col], empty_values=empty_values
        )
        assert non_empty.empty, (
            f"Column {col} contains non-empty values for {data_source} rows"
        )


def test_empty_columns_for_nicht_handelsware_brutto_df(brutto_df: pd.DataFrame) -> None:
    columns_to_check = [
        COL_HAUPTWARENGRUPPE,
        COL_ID_HAUPTWARENGRUPPE,
        COL_WG_EBENE_3_WGI,
        COL_ID_WG_EBENE_3_WGI,
        COL_UNTERWARENGRUPPE,
        COL_ID_UNTERWARENGRUPPE,
        COL_ARTIKELFAMILIE,
        COL_ID_ARTIKELFAMILIE,
        COL_FRUIT_VEG_GROUP,
        COL_ID_FRUIT_VEG_GROUP,
        COL_PLACE_OF_PRODUCTION_ID,
        COL_PLACE_OF_PRODUCTION_NAME,
        COL_PLACE_OF_PRODUCTION_COUNTRY,
        COL_MARKENTYP_HANDELSWARE,
        COL_ABWICKLUNGSART,
    ]

    assert_columns_empty_for_data_source(
        brutto_df,
        DataSource.data_source_nhw,
        columns_to_check,
    )


def test_empty_columns_for_nicht_handelsware_concrete_df(
    concrete_df: pd.DataFrame,
) -> None:
    columns_to_check = [
        COL_HAUPTWARENGRUPPE,
        COL_ID_HAUPTWARENGRUPPE,
        COL_WG_EBENE_3_WGI,
        COL_ID_WG_EBENE_3_WGI,
        COL_UNTERWARENGRUPPE,
        COL_ID_UNTERWARENGRUPPE,
        COL_ARTIKELFAMILIE,
        COL_ID_ARTIKELFAMILIE,
        COL_FRUIT_VEG_GROUP,
        COL_PLACE_OF_PRODUCTION_ID,
        COL_PLACE_OF_PRODUCTION_NAME,
        COL_MARKENTYP_HANDELSWARE,
    ]

    assert_columns_empty_for_data_source(
        concrete_df,
        DataSource.data_source_nhw,
        columns_to_check,
    )


##############################################################
### Tests for Datenerfassung: Handelsware
##############################################################


def test_assert_empty_columns_for_handelsware_brutto_df(
    brutto_df: pd.DataFrame,
) -> None:
    columns_to_check = [
        COL_WG_EBENE_7_KER_POSITION,
        COL_ID_WG_EBENE_7_KER_POSITION,
        COL_WG_EBENE_8_SACHKONTO,
        COL_ID_WG_EBENE_8_SACHKONTO,
        COL_WG_EBENE_9_KOSTENKATEGORIE,
        COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
        COL_BUSINESS_PARTNER_UST_ID,
    ]

    assert_columns_empty_for_data_source(
        brutto_df, DataSource.data_source_hw, columns_to_check
    )


def test_assert_empty_columns_for_handelsware_concrete_df(
    concrete_df: pd.DataFrame,
) -> None:
    columns_to_check = [
        COL_WG_EBENE_7_KER_POSITION,
        COL_ID_WG_EBENE_7_KER_POSITION,
        COL_WG_EBENE_8_SACHKONTO,
        COL_ID_WG_EBENE_8_SACHKONTO,
        COL_WG_EBENE_9_KOSTENKATEGORIE,
        COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
    ]

    assert_columns_empty_for_data_source(
        concrete_df, DataSource.data_source_hw, columns_to_check
    )
