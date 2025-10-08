from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Tuple, TypeAlias

import pandas
from cachetools import LRUCache
from pydantic import BaseModel

from service.data_schema_analysis import (
    DataFrameSchema,
    get_dataframe_metadata,
)

_CACHE_MAX_ITEMS = 16

ColumnsKey: TypeAlias = Tuple[str, ...] | None
CacheKey: TypeAlias = Tuple[str, ColumnsKey, int]

# Global in-process cache with proper typing
_DATASET_CACHE: LRUCache[CacheKey, pandas.DataFrame] = LRUCache(
    maxsize=_CACHE_MAX_ITEMS
)


def _columns_key(columns: list[str] | None) -> ColumnsKey:
    """
    Normalize columns list to a cache-friendly key.
    """
    if columns is None:
        return None
    return tuple(sorted(columns))


def load_dataset_from_path(
    data_path: Path, columns: list[str] | None = None
) -> pandas.DataFrame:
    """
    Load a parquet dataset with centralized LRU caching and optional column selection.

    Caches by (absolute_path, sorted(columns), file_mtime_ns).
    """
    abs_path = data_path.resolve()
    abs_path_str = str(abs_path)

    try:
        mtime_ns = abs_path.stat().st_mtime_ns
    except FileNotFoundError as e:
        mtime_ns = -1
    except PermissionError as e:
        raise PermissionError(f"Cannot access file: {abs_path}") from e

    key: CacheKey = (abs_path_str, _columns_key(columns), mtime_ns)

    cached_df = _DATASET_CACHE.get(key)
    if cached_df is not None:
        return cached_df

    try:
        df = pandas.read_parquet(data_path, columns=columns)
    except Exception as e:
        raise ValueError(f"Cannot read parquet file {abs_path}: {e}") from e

    _DATASET_CACHE[key] = df
    return df


class DataFile(BaseModel):
    file_name: str
    file_path: Path
    description: str

    def add_schema(self) -> "DataFileWithSchema":
        schema = get_schema_for_path(self.file_path)
        return DataFileWithSchema(
            file_name=self.file_name,
            file_path=self.file_path,
            description=self.description,
            data_schema=schema,
        )


class DataFileWithSchema(BaseModel):
    file_name: str
    file_path: Path
    description: str
    data_schema: DataFrameSchema


@lru_cache(maxsize=_CACHE_MAX_ITEMS)
def get_schema_for_path(data_path: Path) -> DataFrameSchema:
    """
    Get schema for a data file with caching based on resolved path and modification time.
    """
    resolved_path = data_path.resolve()

    df = load_dataset_from_path(resolved_path)
    return get_dataframe_metadata(df)


@lru_cache
def get_columns_for_path(data_path: Path) -> list[str]:
    """
    Return deduplicated column names for a data file.

    Uses the pre-generated schema cache to avoid re-reading the dataset when possible.
    """
    resolved_path = data_path.resolve()
    schema = get_schema_for_path(resolved_path)
    return list(schema.columns_metadata.keys())
