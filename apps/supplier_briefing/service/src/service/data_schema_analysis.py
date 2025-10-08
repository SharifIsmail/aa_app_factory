import re
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from service.agent_core.data_management.paths import get_data_dir
from service.risk_columns import RISK_COLUMN_PATTERN


def is_risk_column(column_name: str) -> bool:
    risk_pattern = re.compile(RISK_COLUMN_PATTERN)
    maximales_pattern = re.compile(r"Maximales.*Risiko.*")

    return bool(risk_pattern.match(column_name)) or bool(
        maximales_pattern.match(column_name)
    )


def extract_risk_column_components(risk_columns: list[str]) -> dict[str, set]:
    risk_types = set()
    tiers = set()
    legal_categories = set()

    risk_pattern = re.compile(RISK_COLUMN_PATTERN)
    maximales_pattern = re.compile(r"Maximales (.*?Risiko) (T[0-9n-]+)")

    for col in risk_columns:
        # Handle regular risk columns
        match = risk_pattern.match(col)
        if match:
            risk_types.add(match.group(1))
            tiers.add(match.group(2))
            legal_categories.add(match.group(3))
        else:
            # Handle Maximales columns
            max_match = maximales_pattern.match(col)
            if max_match:
                risk_types.add(f"Maximales {max_match.group(1)}")
                tiers.add(max_match.group(2))

    return {
        "risk_types": risk_types,
        "tiers": tiers,
        "legal_categories": legal_categories,
    }


def get_risk_column_values(df: pd.DataFrame, risk_columns: list[str]) -> set:
    all_values = set()
    for col in risk_columns:
        if col in df.columns:
            unique_vals = df[col].dropna().unique()
            all_values.update(unique_vals)

    return all_values


def generate_risk_summary(df: pd.DataFrame) -> str:
    risk_columns = [col for col in df.columns if is_risk_column(col)]

    if not risk_columns:
        return ""

    components = extract_risk_column_components(risk_columns)
    risk_values = get_risk_column_values(df, risk_columns)

    sorted_values = sorted(risk_values) if risk_values else []

    summary_lines = [
        "RISK ASSESSMENT COLUMNS:",
        "",
        "Column Name Pattern:",
        '"{Risk_Type} {Tier} ({Tier_Description}) - Rechtsposition {Legal_Category}"',
        "",
        "Examples:",
    ]

    example_cols = risk_columns[:3]
    for col in example_cols:
        summary_lines.append(f'- "{col}"')

    summary_lines.extend(
        [
            "",
            "Risk Types:",
        ]
    )

    for risk_type in sorted(components["risk_types"]):
        summary_lines.append(f"- {risk_type}")

    summary_lines.extend(
        [
            "",
            "Supply Chain Tiers:",
        ]
    )

    for tier in sorted(components["tiers"]):
        summary_lines.append(f"- {tier}")

    if components["legal_categories"]:
        summary_lines.extend(
            [
                "",
                "Legal Risk Categories (Rechtsposition):",
            ]
        )

        for category in sorted(components["legal_categories"]):
            summary_lines.append(f"- {category}")

    summary_lines.extend(
        [
            "",
            f"Risk Level Values: {', '.join(map(str, sorted_values))}",
            f"Total: {len(risk_columns)} risk assessment columns",
            "",
        ]
    )

    return "\n".join(summary_lines)


class ColumnMetadata(BaseModel):
    name: str = Field(description="Name of the column")
    value_counts: dict[str | int, int] = Field(
        description="Distribution of values in the column"
    )
    cutoff: int = Field(
        default=5, description="Show full distribution if unique values <= this number"
    )
    example_count: int = Field(
        default=3, description="Number of examples to show if above cutoff"
    )

    @property
    def num_unique_values(self) -> int:
        return len(self.value_counts)

    def to_prompt(self) -> str:
        if self.num_unique_values > self.cutoff:
            return self._format_summary()
        return self._format_full_distribution()

    def _format_summary(self) -> str:
        examples = list(self.value_counts.keys())[: self.example_count]
        return (
            f"Column: '{self.name}'\n"
            f" - Unique values: {self.num_unique_values}\n"
            f" - Example values: {', '.join(f'"{ex}"' for ex in examples)}\n"
        )

    def _format_full_distribution(self) -> str:
        lines = [f"Column: '{self.name}'", "   Value Distribution:"]
        lines.extend(
            f" - '{value}': {count} occurrences"
            for value, count in self.value_counts.items()
        )
        return "\n".join(lines) + "\n"


class IndexLevelMetadata(BaseModel):
    name: str | None = Field(description="Name of the index level (can be None)")
    dtype: str = Field(description="Data type of the index level")
    unique_values: int = Field(description="Number of unique values in this level")
    example_values: list[Any] = Field(description="Example values from this level")
    is_unique: bool = Field(description="Whether all values in this level are unique")


class IndexMetadata(BaseModel):
    is_multi_index: bool = Field(description="Whether this is a multi-index")
    levels: list[IndexLevelMetadata] = Field(
        description="Metadata for each index level"
    )
    total_entries: int = Field(description="Total number of entries in the index")

    def to_prompt(self) -> str:
        if not self.is_multi_index:
            return self._format_single_index()
        return self._format_multi_index()

    def _format_single_index(self) -> str:
        level = self.levels[0]
        index_name = level.name if level.name else "unnamed"
        examples_str = ", ".join(f'"{val}"' for val in level.example_values)

        return (
            f"Index: '{index_name}' (dtype: {level.dtype})\n"
            f" - Total entries: {self.total_entries}\n"
            f" - Unique values: {level.unique_values}\n"
            f" - Is unique: {level.is_unique}\n"
            f" - Example values: {examples_str}\n"
        )

    def _format_multi_index(self) -> str:
        lines = [f"Multi-Index with {len(self.levels)} levels:"]

        for i, level in enumerate(self.levels):
            level_name = level.name if level.name else f"level_{i}"
            examples_str = ", ".join(f'"{val}"' for val in level.example_values)

            lines.extend(
                [
                    f" Level {i}: '{level_name}' (dtype: {level.dtype})",
                    f"  - Unique values: {level.unique_values}",
                    f"  - Is unique: {level.is_unique}",
                    f"  - Example values: {examples_str}",
                ]
            )

        lines.append(f" - Total index entries: {self.total_entries}\n")
        return "\n".join(lines) + "\n"


def _normalize_value_count_key(k: Any) -> str | int:
    if isinstance(k, (str, int)):
        return k
    if isinstance(k, pd.Timestamp):
        return k.isoformat()
    if pd.isna(k):
        return "NaN"
    return str(k)


def get_metadata_for_column(
    df: pd.DataFrame, column_name: str, cutoff: int = 5, example_count: int = 3
) -> ColumnMetadata:
    counts = df[column_name].value_counts(dropna=False)
    normalized_counts: dict[str | int, int] = {
        _normalize_value_count_key(k): int(v) for k, v in counts.items()
    }
    return ColumnMetadata(
        name=column_name,
        value_counts=normalized_counts,
        cutoff=cutoff,
        example_count=example_count,
    )


def get_index_metadata(df: pd.DataFrame, example_count: int = 3) -> IndexMetadata:
    index = df.index
    is_multi = isinstance(index, pd.MultiIndex)

    if is_multi:
        levels_metadata = []
        for i in range(index.nlevels):
            level_values = index.get_level_values(i)
            level_name = index.names[i]

            unique_vals = level_values.unique()
            example_vals = unique_vals[:example_count].tolist()

            levels_metadata.append(
                IndexLevelMetadata(
                    name=str(level_name) if level_name is not None else None,
                    dtype=str(level_values.dtype),
                    unique_values=len(unique_vals),
                    example_values=example_vals,
                    is_unique=len(unique_vals) == len(level_values),
                )
            )
    else:
        unique_vals = index.unique()
        example_vals = unique_vals[:example_count].tolist()

        levels_metadata = [
            IndexLevelMetadata(
                name=str(index.name) if index.name is not None else None,
                dtype=str(index.dtype),
                unique_values=len(unique_vals),
                example_values=example_vals,
                is_unique=len(unique_vals) == len(index),
            )
        ]

    return IndexMetadata(
        is_multi_index=is_multi, levels=levels_metadata, total_entries=len(index)
    )


class DataFrameSchema(BaseModel):
    columns_metadata: dict[str, ColumnMetadata] = Field(
        description="Metadata for each column in the DataFrame"
    )
    index_metadata: IndexMetadata = Field(
        description="Metadata for the DataFrame's index"
    )
    risk_summary: str = Field(
        default="", description="Summary of risk assessment columns"
    )

    def to_prompt(self) -> str:
        lines = ["DataFrame Structure:"]

        lines.append("INDEX INFORMATION:")
        lines.append(self.index_metadata.to_prompt())

        non_risk_columns = [
            col_meta
            for col_name, col_meta in self.columns_metadata.items()
            if not is_risk_column(col_name)
        ]

        if non_risk_columns:
            lines.append("COLUMN INFORMATION:")
            lines.extend(
                column_metadata.to_prompt() for column_metadata in non_risk_columns
            )

        if self.risk_summary:
            lines.append(self.risk_summary)

        return "\n".join(lines)


def get_all_columns_metadata(
    df: pd.DataFrame, cutoff: int = 5, example_count: int = 3
) -> str:
    return "\n".join(
        get_metadata_for_column(
            df=df, column_name=column, cutoff=cutoff, example_count=example_count
        ).to_prompt()
        for column in df.columns
    )


def get_dataframe_metadata(
    df: pd.DataFrame, cutoff: int = 5, example_count: int = 3
) -> DataFrameSchema:
    columns_metadata = {
        column: get_metadata_for_column(
            df=df, column_name=column, cutoff=cutoff, example_count=example_count
        )
        for column in df.columns
    }

    index_metadata = get_index_metadata(df=df, example_count=example_count)
    risk_summary = generate_risk_summary(df=df)

    return DataFrameSchema(
        columns_metadata=columns_metadata,
        index_metadata=index_metadata,
        risk_summary=risk_summary,
    )


def process_parquet_file(parquet_path: Path) -> None:
    print(f"Processing {parquet_path.name}...")

    try:
        df = pd.read_parquet(parquet_path)
        schema = get_dataframe_metadata(df)
        schema_text = schema.to_prompt()

        output_path = parquet_path.with_suffix(".schema.txt")
        output_path.write_text(schema_text, encoding="utf-8")

        print(f"✓ Schema saved to {output_path.name}")

    except Exception as e:
        print(f"✗ Error processing {parquet_path.name}: {e}")


def generate_schema_files() -> None:
    print("=== Generating Schema Files For Debugging Purposes ===")

    data_dir = get_data_dir()
    parquet_files = list(data_dir.glob("*.parquet"))

    if not parquet_files:
        print("No parquet files found in data directory")
        return

    print(f"Found {len(parquet_files)} parquet files")

    for parquet_file in parquet_files:
        process_parquet_file(parquet_file)

    print("✓ Schema generation complete")


if __name__ == "__main__":
    generate_schema_files()
