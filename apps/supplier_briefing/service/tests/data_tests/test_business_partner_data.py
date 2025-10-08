import pandas as pd
import pytest

from service.agent_core.data_management.columns import (
    COL_BRUTTO_PRIORISIERUNG,
    COL_BUSINESS_PARTNER_NAME,
    COL_COUNTRY,
    COL_DATA_SOURCE,
    COL_KONKRETE_PRIORISIERUNG,
    COL_NETTO_PRIORISIERUNG,
    COL_REVENUE_THRESHOLD,
    COL_SCHWARZ_GROUP_FLAG,
    COL_SCHWARZBESCHAFFUNG,
)
from service.data_preparation import assert_column_depends_on_other_column


@pytest.mark.parametrize(
    "column",
    [
        COL_SCHWARZBESCHAFFUNG,
        COL_SCHWARZ_GROUP_FLAG,
        COL_DATA_SOURCE,
        COL_BRUTTO_PRIORISIERUNG,
        COL_REVENUE_THRESHOLD,
    ],
)
def test_brutto_df_business_partner_metadata_columns_unique_per_id(
    brutto_df: pd.DataFrame, column: str
) -> None:
    assert_column_depends_on_other_column(brutto_df, column)


@pytest.mark.parametrize(
    "column",
    [
        COL_BUSINESS_PARTNER_NAME,
        COL_SCHWARZBESCHAFFUNG,
        COL_SCHWARZ_GROUP_FLAG,
        COL_DATA_SOURCE,
        COL_NETTO_PRIORISIERUNG,
        COL_KONKRETE_PRIORISIERUNG,
    ],
)
def test_concrete_df_business_partner_metadata_columns_unique_per_id(
    concrete_df: pd.DataFrame, column: str
) -> None:
    assert_column_depends_on_other_column(concrete_df, column)


@pytest.mark.parametrize(
    "column",
    [
        COL_BUSINESS_PARTNER_NAME,
        COL_COUNTRY,
        COL_SCHWARZBESCHAFFUNG,
        COL_SCHWARZ_GROUP_FLAG,
        COL_DATA_SOURCE,
        COL_NETTO_PRIORISIERUNG,
        COL_KONKRETE_PRIORISIERUNG,
        COL_REVENUE_THRESHOLD,
    ],
)
def test_transactions_df_business_partner_metadata_columns_unique_per_id(
    transactions_df: pd.DataFrame, column: str
) -> None:
    assert_column_depends_on_other_column(transactions_df, column)
