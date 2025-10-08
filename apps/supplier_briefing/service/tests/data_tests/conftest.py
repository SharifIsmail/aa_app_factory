import pandas as pd
import pytest

from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path
from service.data_preparation import (
    BRUTTO_FILE_CLEANED_PARQUET,
    BRUTTO_FILE_PARQUET,
    BUSINESS_PARTNERS_PARQUET,
    CONCRETE_FILE_CLEANED_PARQUET,
    CONCRETE_FILE_PARQUET,
    TRANSACTIONS_PARQUET,
)


@pytest.fixture
def brutto_df() -> pd.DataFrame:
    return load_dataset_from_path(DATA_DIR / BRUTTO_FILE_PARQUET)


@pytest.fixture
def brutto_df_cleaned() -> pd.DataFrame:
    return load_dataset_from_path(DATA_DIR / BRUTTO_FILE_CLEANED_PARQUET)


@pytest.fixture
def concrete_df() -> pd.DataFrame:
    return load_dataset_from_path(DATA_DIR / CONCRETE_FILE_PARQUET)


@pytest.fixture
def concrete_df_cleaned() -> pd.DataFrame:
    return load_dataset_from_path(DATA_DIR / CONCRETE_FILE_CLEANED_PARQUET)


@pytest.fixture
def transactions_df() -> pd.DataFrame:
    return load_dataset_from_path(DATA_DIR / TRANSACTIONS_PARQUET)


@pytest.fixture
def business_partners_df() -> pd.DataFrame:
    return load_dataset_from_path(DATA_DIR / BUSINESS_PARTNERS_PARQUET)
