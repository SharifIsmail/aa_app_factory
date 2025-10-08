from functools import lru_cache

import pandas as pd

from service.agent_core.constants import DATA_SOURCE_HW, DATA_SOURCE_NHW
from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_COUNTRY,
    COL_DATA_SOURCE,
)
from service.agent_core.data_management.paths import get_data_dir
from service.data_loading import load_dataset_from_path
from service.data_preparation import TRANSACTIONS_PARQUET


class Transactions:
    @lru_cache
    @staticmethod
    def df() -> pd.DataFrame:
        return load_dataset_from_path(get_data_dir() / TRANSACTIONS_PARQUET)

    @staticmethod
    def number_of_rows() -> int:
        return Transactions.df().shape[0]

    @staticmethod
    def number_of_trading_goods() -> int:
        df = Transactions.df()
        return df[df[COL_DATA_SOURCE] == DATA_SOURCE_HW].shape[0]

    @staticmethod
    def number_of_non_trading_goods() -> int:
        df = Transactions.df()
        return df[df[COL_DATA_SOURCE] == DATA_SOURCE_NHW].shape[0]

    @staticmethod
    def number_of_unique_business_partners() -> int:
        df = Transactions.df()
        return df[COL_BUSINESS_PARTNER_ID].nunique()

    @staticmethod
    def number_of_unique_countries() -> int:
        return Transactions.df()[COL_COUNTRY].nunique()
