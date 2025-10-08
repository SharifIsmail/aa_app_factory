from typing import Sequence

import pandas as pd
import pytest
from pydantic import BaseModel

from service.agent_core.constants import DATA_SOURCE_HW, DATA_SOURCE_NHW
from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_ARTIKELFAMILIE,
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_UST_ID,
    COL_DATA_SOURCE,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_ID_ARTICLE_NAME,
    COL_ID_ARTICLE_UNIQUE,
    COL_ID_WG_EBENE_8_SACHKONTO,
    COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
    COL_MARKENTYP_HANDELSWARE,
    COL_PROCUREMENT_UNIT,
    COL_REVENUE_TOTAL,
    COL_WG_EBENE_7_KER_POSITION,
)
from tests.data_tests.utils import compute_primary_key_values

PRIMARY_KEY_COMPONENT_COLUMNS_BASE: list[str] = [
    COL_BUSINESS_PARTNER_ID,
    COL_PROCUREMENT_UNIT,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
]

HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS: list[str] = list(
    PRIMARY_KEY_COMPONENT_COLUMNS_BASE
    + [
        COL_REVENUE_TOTAL,
        COL_MARKENTYP_HANDELSWARE,
        COL_ARTIKELFAMILIE,
        COL_ARTICLE_NAME,
        COL_ID_ARTICLE_NAME,
    ]
)

NICHT_HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS: list[str] = list(
    PRIMARY_KEY_COMPONENT_COLUMNS_BASE
    + [
        COL_WG_EBENE_7_KER_POSITION,
        COL_ID_WG_EBENE_8_SACHKONTO,
        COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
    ]
)


class PrimaryKeyScenario(BaseModel):
    name: str
    fixture_name: str
    data_source: str
    primary_key_columns: Sequence[str]
    columns_to_drop: Sequence[str]
    expected_duplicate_keys: int
    expected_duplicate_rows: int


PRIMARY_KEY_SCENARIOS: list[PrimaryKeyScenario] = [
    PrimaryKeyScenario(
        name="brutto_handelsware",
        fixture_name="brutto_df_cleaned",
        data_source=DATA_SOURCE_HW,
        primary_key_columns=HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS,
        columns_to_drop=[COL_BUSINESS_PARTNER_UST_ID],
        expected_duplicate_keys=116,
        expected_duplicate_rows=240,
    ),
    PrimaryKeyScenario(
        name="brutto_nebenhandelsware",
        fixture_name="brutto_df_cleaned",
        data_source=DATA_SOURCE_NHW,
        primary_key_columns=NICHT_HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS,
        columns_to_drop=[COL_BUSINESS_PARTNER_UST_ID],
        expected_duplicate_keys=6,
        expected_duplicate_rows=15,
    ),
    PrimaryKeyScenario(
        name="concrete_handelsware",
        fixture_name="concrete_df_cleaned",
        data_source=DATA_SOURCE_HW,
        primary_key_columns=HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS,
        columns_to_drop=[COL_ID_ARTICLE_UNIQUE],
        expected_duplicate_keys=42,
        expected_duplicate_rows=84,
    ),
    PrimaryKeyScenario(
        name="concrete_nebenhandelsware",
        fixture_name="concrete_df_cleaned",
        data_source=DATA_SOURCE_NHW,
        primary_key_columns=NICHT_HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS,
        columns_to_drop=[COL_ID_ARTICLE_UNIQUE],
        expected_duplicate_keys=1,
        expected_duplicate_rows=2,
    ),
]


@pytest.mark.parametrize(
    "primary_key_scenario",
    PRIMARY_KEY_SCENARIOS,
    ids=[scenario.name for scenario in PRIMARY_KEY_SCENARIOS],
)
def test_pseudo_primary_keys_produces_duplicates(
    request: pytest.FixtureRequest, primary_key_scenario: PrimaryKeyScenario
) -> None:
    df: pd.DataFrame = request.getfixturevalue(primary_key_scenario.fixture_name)
    df_filtered_for_data_source = df[
        df[COL_DATA_SOURCE] == primary_key_scenario.data_source
    ].copy()
    assert not df_filtered_for_data_source.empty

    columns_to_drop = [
        column
        for column in primary_key_scenario.columns_to_drop
        if column in df_filtered_for_data_source.columns
    ]
    df_filtered_for_data_source_dropped_columns = (
        df_filtered_for_data_source.drop(columns=columns_to_drop)
        .drop_duplicates()
        .reset_index(drop=True)
    )

    for column in primary_key_scenario.primary_key_columns:
        assert column in df_filtered_for_data_source_dropped_columns.columns

    primary_key_series = compute_primary_key_values(
        df_filtered_for_data_source_dropped_columns,
        primary_key_scenario.primary_key_columns,
    )
    duplicates = primary_key_series.value_counts()
    duplicate_keys = duplicates[duplicates > 1]

    assert len(duplicate_keys) == primary_key_scenario.expected_duplicate_keys
    assert int(duplicate_keys.sum()) == primary_key_scenario.expected_duplicate_rows


@pytest.mark.parametrize(
    "primary_key_columns",
    [
        HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS,
        NICHT_HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS,
    ],
    ids=["Handelsware", "Nicht-Handelsware"],
)
def test_primary_key_columns_present_in_brutto_and_concrete_files(
    request: pytest.FixtureRequest, primary_key_columns: Sequence[str]
) -> None:
    for fixture_name in ("brutto_df_cleaned", "concrete_df_cleaned"):
        df: pd.DataFrame = request.getfixturevalue(fixture_name)
        missing_columns = [
            column for column in primary_key_columns if column not in df.columns
        ]
        assert not missing_columns, (
            f"{fixture_name} is missing primary key columns: {missing_columns}"
        )
