import hashlib
from typing import Iterable

import pandas as pd

from service.agent_core.data_management.columns import EMPTY_VALUES


def filter_for_non_empty_values(
    series: pd.Series, empty_values: list[str | None] = EMPTY_VALUES
) -> pd.Series:
    """Returns subseries of non-empty values.

    Values listed in `empty_values` are treated case-insensitively
    """
    empty_values_lower = [str(val).lower() for val in empty_values]
    mask = ~series.astype(str).str.lower().isin(empty_values_lower)

    return series[mask].dropna()


def is_empty_value(value_str: str) -> bool:
    """Check if a string value should be considered empty based on EMPTY_VALUES."""
    normalized = value_str.strip().lower()
    return any(
        normalized == empty_val.strip().lower()
        for empty_val in EMPTY_VALUES
        if isinstance(empty_val, str) and empty_val.strip()
    )


def normalize_value_for_primary_key(value: object) -> str:
    if pd.isna(value) or value is None:
        return "<NA>"
    if isinstance(value, str):
        normalized = value.strip()
        if is_empty_value(normalized):
            return "<NA>"
        return normalized
    value_str = str(value)
    if is_empty_value(value_str):
        return "<NA>"
    return value_str


def compute_primary_key_values(df: pd.DataFrame, columns: Iterable[str]) -> pd.Series:
    normalized_values = df.loc[:, list(columns)].map(normalize_value_for_primary_key)
    return normalized_values.apply(
        lambda row: hashlib.sha1("||".join(row.to_list()).encode("utf-8")).hexdigest(),
        axis=1,
    )
