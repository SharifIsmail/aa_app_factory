import pandas as pd


def select_columns_with_differences(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return columns whose values differ across rows.

    A column is kept when it contains at least two distinct values (NaNs included).
    If no column varies, an empty dataframe sharing the original index is returned.
    """

    differing_columns = [
        column
        for column in dataframe.columns
        if dataframe[column].nunique(dropna=False) > 1
    ]

    return dataframe.loc[:, differing_columns].copy()
