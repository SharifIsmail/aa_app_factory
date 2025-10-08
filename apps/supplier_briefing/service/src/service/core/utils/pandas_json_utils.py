import json
from io import StringIO
from typing import Any, Dict, Hashable

import pandas as pd
from loguru import logger


def _serialize_index_metadata(obj: pd.DataFrame | pd.Series) -> list[Hashable]:
    if isinstance(obj.index, pd.MultiIndex):
        return list(obj.index.names)
    else:
        index_name = obj.index.name
        index_names = [index_name] if index_name is not None else []
        return index_names


def _serialize_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    json_str = df.to_json(orient="split", date_format="iso")
    result = {
        "data": json.loads(json_str),
        "type": "DataFrame",
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "index_names": _serialize_index_metadata(df),
    }
    return result


def _serialize_series(series: pd.Series) -> Dict[str, Any]:
    json_str = series.to_json(orient="split", date_format="iso")
    result = {
        "data": json.loads(json_str),
        "type": "Series",
        "dtype": str(series.dtype),
        "index_names": _serialize_index_metadata(series),
    }
    return result


def serialize_pandas_object_to_json(obj: pd.DataFrame | pd.Series) -> Dict[str, Any]:
    if isinstance(obj, pd.DataFrame):
        return _serialize_dataframe(obj)
    elif isinstance(obj, pd.Series):
        return _serialize_series(obj)
    else:
        raise ValueError(f"Unsupported type: {type(obj)}")


def _has_multiindex(json_data: Dict[str, Any]) -> bool:
    index = json_data.get("index", [])
    return len(index) > 0 and isinstance(index[0], list)


def _deserialize_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    json_data = data["data"]

    if _has_multiindex(json_data):
        index = pd.MultiIndex.from_tuples(json_data["index"])
        df = pd.DataFrame(
            data=json_data["data"], index=index, columns=json_data["columns"]
        )
    else:
        json_str = json.dumps(json_data)
        df = pd.read_json(StringIO(json_str), orient="split")

    # Restore index names
    if "index_names" in data and data["index_names"]:
        if isinstance(df.index, pd.MultiIndex):
            df.index.names = data["index_names"]
        elif len(data["index_names"]) > 0:
            df.index.name = data["index_names"][0]

    # Restore dtypes
    for col, dtype_str in data.get("dtypes", {}).items():
        if dtype_str == "category" and df[col].dtype == "object":
            df[col] = df[col].astype("category")

    return df


def _deserialize_series(data: Dict[str, Any]) -> pd.Series:
    json_data = data["data"]

    if _has_multiindex(json_data):
        index = pd.MultiIndex.from_tuples(json_data["index"])
        series = pd.Series(data=json_data["data"], index=index)
    else:
        json_str = json.dumps(json_data)
        series = pd.read_json(StringIO(json_str), typ="series", orient="split")

    # Restore index names
    if "index_names" in data and data["index_names"]:
        if isinstance(series.index, pd.MultiIndex):
            series.index.names = data["index_names"]
        elif len(data["index_names"]) > 0:
            series.index.name = data["index_names"][0]

    return series


def deserialize_pandas_object_from_json(
    data: Dict[str, Any],
) -> pd.DataFrame | pd.Series | None:
    if data["type"] == "DataFrame":
        return _deserialize_dataframe(data)
    elif data["type"] == "Series":
        return _deserialize_series(data)
    else:
        logger.warning(f"Unsupported type: {type(data)}")
        return None
