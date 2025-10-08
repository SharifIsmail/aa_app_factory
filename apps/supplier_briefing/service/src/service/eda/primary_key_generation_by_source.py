from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence

import pandas as pd
from loguru import logger

from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_ARTIKELFAMILIE,
    COL_BUSINESS_PARTNER_ID,
    COL_DATA_SOURCE,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_ID_ARTICLE_NAME,
    COL_ID_ARTICLE_UNIQUE,
    COL_ID_WG_EBENE_8_SACHKONTO,
    COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
    COL_MARKENTYP_HANDELSWARE,
    COL_PRIMARY_KEY,
    COL_PROCUREMENT_UNIT,
    COL_REVENUE_TOTAL,
    COL_WG_EBENE_7_KER_POSITION,
    EMPTY_VALUES,
)
from service.agent_core.data_management.paths import get_data_dir
from service.data_loading import load_dataset_from_path
from service.data_preparation import (
    BRUTTO_FILE_CLEANED_PARQUET,
    CONCRETE_FILE_CLEANED_PARQUET,
)
from tests.data_tests.utils import compute_primary_key_values

PRIMARY_KEY_COMPONENT_COLUMNS_BASE = [
    COL_BUSINESS_PARTNER_ID,
    COL_PROCUREMENT_UNIT,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
]


HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS = list(
    PRIMARY_KEY_COMPONENT_COLUMNS_BASE
    + [
        COL_REVENUE_TOTAL,  # This can most likely be removed once we take care of TBAF-300
        COL_MARKENTYP_HANDELSWARE,
        COL_ARTIKELFAMILIE,
        COL_ARTICLE_NAME,
        COL_ID_ARTICLE_NAME,
        # COL_SUPPLIED_UNIT,
        # Issue: the "Belieferte Einheit" in the "concrete_file" contains only a reference to "Siehe Brutto-Datei"
        # which we cannot resolve. This yields more duplicates than necessary, because we cannot use this column in the
        # primary key across both brutto and concrete file
        # If we could add the COL_SUPPLIED_UNIT here, it would reduce the duplicates again quite a lot
        # In fact, using the COL_SUPPLIED_UNIT here yields NO duplicates in the brutto-handelsware case
    ]
)
NICHT_HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS = list(
    PRIMARY_KEY_COMPONENT_COLUMNS_BASE
    + [
        COL_WG_EBENE_7_KER_POSITION,
        COL_ID_WG_EBENE_8_SACHKONTO,
        COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
    ]
)

_EMPTY_VALUE_MARKERS = {
    value.strip().lower()
    for value in EMPTY_VALUES
    if isinstance(value, str) and value.strip()
}


class DatasetKind(str, Enum):
    BRUTTO = "brutto"
    CONCRETE = "concrete"


class DataSourceKind(str, Enum):
    HANDELSWARE = "Datenerfassung Handelsware (HW)"
    NICHT_HANDELSWARE = "Datenerfassung Nicht-Handelsware (NHW)"


@dataclass(frozen=True)
class DatasetConfig:
    cleaned_file_name: str
    columns_to_drop: list[str]


DATASET_CONFIG = {
    DatasetKind.BRUTTO: DatasetConfig(
        cleaned_file_name=BRUTTO_FILE_CLEANED_PARQUET,
        columns_to_drop=[],
    ),
    DatasetKind.CONCRETE: DatasetConfig(
        cleaned_file_name=CONCRETE_FILE_CLEANED_PARQUET,
        columns_to_drop=[COL_ID_ARTICLE_UNIQUE],
    ),
}


class PrimaryKeyGenerationBySource:
    def __init__(
        self,
        handelsware_columns: Sequence[str] | None = None,
        nicht_handelsware_columns: Sequence[str] | None = None,
    ) -> None:
        self.data_dir = get_data_dir()
        self.primary_key_columns_by_source = {
            DataSourceKind.HANDELSWARE: list(
                handelsware_columns or HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS
            ),
            DataSourceKind.NICHT_HANDELSWARE: list(
                nicht_handelsware_columns
                or NICHT_HANDELSWARE_PRIMARY_KEY_COMPONENT_COLUMNS
            ),
        }

    def run(self, dataset: DatasetKind, data_source: DataSourceKind) -> pd.DataFrame:
        logger.info(
            "Starting primary key generation for dataset '{}' and data source '{}'.",
            dataset.value,
            data_source.value,
        )
        cleaned_df = self._load_cleaned_dataframe(dataset)
        self._check_primary_key_columns_present(cleaned_df, dataset, data_source)

        subset_df = self._select_data_source_subset(cleaned_df, data_source)
        prepared_df = self._prepare_dataframe(subset_df, dataset)
        with_primary_key = self._add_primary_key_column(
            prepared_df, dataset, data_source
        )
        self._ensure_primary_key_column_added(with_primary_key)

        self._log_duplicate_stats(with_primary_key)

        output_path = self.get_output_path(dataset, data_source)
        self._write_dataframe(with_primary_key, output_path)
        logger.info("Wrote dataframe with primary key to '{}'.", output_path.name)
        return with_primary_key

    def _load_cleaned_dataframe(self, dataset: DatasetKind) -> pd.DataFrame:
        config = DATASET_CONFIG[dataset]
        path = self.data_dir / config.cleaned_file_name
        return load_dataset_from_path(path)

    def _check_primary_key_columns_present(
        self,
        df: pd.DataFrame,
        dataset: DatasetKind,
        data_source: DataSourceKind,
    ) -> None:
        config = DATASET_CONFIG[dataset]
        required_columns = list(self.primary_key_columns_by_source[data_source])
        required_columns.append(COL_DATA_SOURCE)

        missing_columns = [
            column for column in required_columns if column not in df.columns
        ]
        if missing_columns:
            raise AssertionError(
                "Missing required columns in cleaned dataset '{}': {}".format(
                    config.cleaned_file_name,
                    ", ".join(missing_columns),
                )
            )

    @staticmethod
    def _select_data_source_subset(
        df: pd.DataFrame, data_source: DataSourceKind
    ) -> pd.DataFrame:
        data_source_column = df[COL_DATA_SOURCE]
        mask = data_source_column == data_source.value
        filtered_df = df.loc[mask].copy()
        if filtered_df.empty:
            raise ValueError(f"No rows found for data source {data_source.value!r}.")
        return filtered_df

    @staticmethod
    def _prepare_dataframe(df: pd.DataFrame, dataset: DatasetKind) -> pd.DataFrame:
        config = DATASET_CONFIG[dataset]
        without_columns = df.drop(columns=config.columns_to_drop).copy()
        return without_columns.drop_duplicates().reset_index(drop=True)

    def _add_primary_key_column(
        self,
        df: pd.DataFrame,
        dataset: DatasetKind,
        data_source: DataSourceKind,
    ) -> pd.DataFrame:
        columns = self._primary_key_columns(data_source)
        self._ensure_columns_present(df, columns, "prepared dataframe")
        dataframe = df.copy()
        primary_key_values = compute_primary_key_values(dataframe, columns)
        dataframe.insert(0, COL_PRIMARY_KEY, primary_key_values)
        return dataframe

    @staticmethod
    def _ensure_primary_key_column_added(df: pd.DataFrame) -> None:
        if df.columns[0] != COL_PRIMARY_KEY:
            raise AssertionError("Primary key column is not the first column.")
        if df[COL_PRIMARY_KEY].dtype != object:
            raise AssertionError("Primary key column dtype is not object.")

    @staticmethod
    def _log_duplicate_stats(df: pd.DataFrame) -> None:
        duplicate_counts = df[COL_PRIMARY_KEY].value_counts()
        duplicates = duplicate_counts[duplicate_counts > 1]
        logger.info(
            "Found {} duplicate primary keys out of {} rows.",
            int(duplicates.size),
            int(len(df)),
        )
        if not duplicates.empty:
            logger.warning(
                "Primary key duplicates detected for hashes: {}",
                ", ".join(duplicates.index.tolist()),
            )

    def get_output_path(
        self, dataset: DatasetKind, data_source: DataSourceKind
    ) -> Path:
        """Return the output parquet path for the given dataset/source."""
        suffix = (
            "handelsware"
            if data_source == DataSourceKind.HANDELSWARE
            else "nicht_handelsware"
        )
        file_name = f"{dataset.value}_{suffix}_cleaned_with_primary_key.parquet"
        return self.data_dir / file_name

    @staticmethod
    def _ensure_columns_present(
        df: pd.DataFrame, columns: Sequence[str], dataset_name: str
    ) -> None:
        missing_columns = [column for column in columns if column not in df.columns]
        if missing_columns:
            raise KeyError(
                f"Missing required columns in {dataset_name}: {', '.join(missing_columns)}"
            )

    def _primary_key_columns(self, data_source: DataSourceKind) -> list[str]:
        base_columns = self.primary_key_columns_by_source[data_source]
        return list(base_columns)

    def get_primary_key_columns(
        self, dataset: DatasetKind, data_source: DataSourceKind
    ) -> list[str]:
        """Return the ordered primary key columns for the given dataset/source."""
        return self._primary_key_columns(data_source)

    @staticmethod
    def _write_dataframe(df: pd.DataFrame, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path)
