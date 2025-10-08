from collections.abc import Sequence
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from loguru import logger

from eda.select_columns_with_differences import select_columns_with_differences
from service.agent_core.data_management.columns import COL_PRIMARY_KEY
from service.eda.primary_key_generation_by_source import (
    DatasetKind,
    DataSourceKind,
    PrimaryKeyGenerationBySource,
)
from tests.data_tests.utils import compute_primary_key_values

DuplicateStats = Tuple[int, int]

ALL_COMBINATIONS: Tuple[Tuple[DatasetKind, DataSourceKind], ...] = (
    (DatasetKind.BRUTTO, DataSourceKind.HANDELSWARE),
    (DatasetKind.BRUTTO, DataSourceKind.NICHT_HANDELSWARE),
    (DatasetKind.CONCRETE, DataSourceKind.HANDELSWARE),
    (DatasetKind.CONCRETE, DataSourceKind.NICHT_HANDELSWARE),
)

OVERLAP_COMPARISONS: Tuple[
    Tuple[Tuple[DatasetKind, DataSourceKind], Tuple[DatasetKind, DataSourceKind]],
    ...,
] = (
    (
        (DatasetKind.BRUTTO, DataSourceKind.HANDELSWARE),
        (DatasetKind.CONCRETE, DataSourceKind.HANDELSWARE),
    ),
    (
        (DatasetKind.BRUTTO, DataSourceKind.NICHT_HANDELSWARE),
        (DatasetKind.CONCRETE, DataSourceKind.NICHT_HANDELSWARE),
    ),
)


def run_primary_key_generation_checks(
    handelsware_columns: Sequence[str] | None = None,
    nicht_handelsware_columns: Sequence[str] | None = None,
) -> Dict[Tuple[DatasetKind, DataSourceKind], pd.DataFrame]:
    """Run primary-key generation and validation for all dataset/source combos."""
    generator = PrimaryKeyGenerationBySource(
        handelsware_columns=handelsware_columns,
        nicht_handelsware_columns=nicht_handelsware_columns,
    )
    results: Dict[Tuple[DatasetKind, DataSourceKind], pd.DataFrame] = {}
    duplicate_stats_by_file: Dict[str, DuplicateStats] = {}

    for dataset, data_source in ALL_COMBINATIONS:
        df_with_pk = generator.run(dataset, data_source)
        results[(dataset, data_source)] = df_with_pk

        primary_key_columns = generator.get_primary_key_columns(dataset, data_source)
        logger.info(
            f"Primary key columns for {dataset.value} and {data_source.value}: {primary_key_columns}"
        )
        duplicate_stats = check_primary_key_uniqueness(
            df_with_pk,
            dataset,
            data_source,
            primary_key_columns,
        )

        file_name = generator.get_output_path(dataset, data_source).name
        duplicate_stats_by_file[file_name] = duplicate_stats

        key_columns = generator.get_primary_key_columns(dataset, data_source)
        check_primary_key_component_redundancy(
            df_with_pk,
            key_columns,
            dataset,
            data_source,
        )

    _log_duplicate_overview(duplicate_stats_by_file)

    return results


def check_primary_key_uniqueness(
    df_with_primary_key: pd.DataFrame,
    dataset: DatasetKind,
    data_source: DataSourceKind,
    primary_key_columns: Sequence[str],
) -> DuplicateStats:
    duplicate_key_count, total_duplicate_rows = _duplicate_stats_for_columns(
        df_with_primary_key,
        primary_key_columns,
        str(dataset.value) + "_" + str(data_source.value),
    )

    if duplicate_key_count == 0:
        logger.info(
            "Primary key unique for dataset '{}' and data source '{}'.",
            dataset.value,
            data_source.value,
        )
        return duplicate_key_count, total_duplicate_rows

    logger.warning(
        "Primary key duplicates detected for dataset '{}' and data source '{}': {} duplicate keys, {} duplicate rows.",
        dataset.value,
        data_source.value,
        duplicate_key_count,
        total_duplicate_rows,
    )
    counts = df_with_primary_key[COL_PRIMARY_KEY].value_counts()
    duplicates = counts[counts > 1]
    duplicate_summary = ", ".join(
        f"{hash_value} ({count})" for hash_value, count in duplicates.items()
    )
    logger.warning("Duplicate hashes: {}", duplicate_summary)
    return duplicate_key_count, total_duplicate_rows


def _log_duplicate_overview(duplicate_stats_by_file: Dict[str, DuplicateStats]) -> None:
    if not duplicate_stats_by_file:
        return

    logger.info("Primary key duplicate overview by file:")
    for file_name, (
        duplicate_key_count,
        total_duplicate_rows,
    ) in duplicate_stats_by_file.items():
        logger.info(
            "{} -> {} duplicate keys, {} duplicate rows.",
            file_name,
            duplicate_key_count,
            total_duplicate_rows,
        )


def check_primary_key_component_redundancy(
    df: pd.DataFrame,
    candidate_columns: Sequence[str],
    dataset: DatasetKind,
    data_source: DataSourceKind,
) -> None:
    baseline_stats = _duplicate_stats_for_columns(df, candidate_columns)
    logger.info(
        "Baseline duplicate stats for {}/{}: {}",
        dataset.value,
        data_source.value,
        baseline_stats,
    )

    for column in candidate_columns:
        reduced_columns = [
            candidate for candidate in candidate_columns if candidate != column
        ]
        stats = _duplicate_stats_for_columns(df, reduced_columns)
        logger.info(
            "Removing '{}' -> duplicate stats {} for {}/{}",
            column,
            stats,
            dataset.value,
            data_source.value,
        )
        if stats == baseline_stats:
            logger.info(
                "Duplicate stats unchanged after removing '{}' for {}/{}.",
                column,
                dataset.value,
                data_source.value,
            )


def _write_duplicate_analysis_file(
    df: pd.DataFrame,
    duplicate_counts: pd.Series,
    df_identifier: str,
) -> None:
    """Write duplicate analysis results to a markdown file."""
    output_dir = Path("duplicates")
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / f"duplicate_value_columns_{df_identifier}.md"

    # Collect all difference columns across all duplicate keys
    difference_column_counts: dict[str, int] = {}
    for duplicate_key in duplicate_counts.keys():
        diff_df = select_columns_with_differences(
            df[df[COL_PRIMARY_KEY] == duplicate_key]
        )
        for col_name in diff_df.columns:
            difference_column_counts[col_name] = (
                difference_column_counts.get(col_name, 0) + 1
            )

    with open(file_path, "w") as file:
        file.write(50 * "=" + "\n")
        file.write(f"## Summary:\n")
        file.write(f"* **Number of duplicate keys**: {duplicate_counts.size}\n")
        file.write(f"* **Total duplicate rows**: {duplicate_counts.sum()}\n\n")

        if difference_column_counts:
            file.write("### Columns causing duplicates (frequency):\n")
            sorted_columns = sorted(
                difference_column_counts.items(), key=lambda x: x[1], reverse=True
            )
            for col_name, frequency in sorted_columns:
                file.write(f"- **{col_name}**: {frequency} times\n")
            file.write("\n")

        file.write(50 * "=" + "\n")

        for duplicate_key in duplicate_counts.keys():
            file.write(f"### Duplicate Key: {duplicate_key}\n\n")

            file.write("#### Columns with Differences:\n\n")
            diff_df = select_columns_with_differences(
                df[df[COL_PRIMARY_KEY] == duplicate_key]
            )
            file.write(diff_df.to_markdown(index=False))
            file.write("\n\n")

            file.write("#### All Columns:\n\n")
            full_df = df[df[COL_PRIMARY_KEY] == duplicate_key]
            file.write(full_df.to_markdown(index=False))
            file.write("\n\n")


def _duplicate_stats_for_columns(
    df: pd.DataFrame, columns: Sequence[str], df_identifier: str | None = None
) -> Tuple[int, int]:
    """Return count of duplicate keys and total duplicate rows for the given columns."""
    df_without_primary_key = df.drop(columns=[COL_PRIMARY_KEY])

    primary_key_values = compute_primary_key_values(df_without_primary_key, columns)

    counts = primary_key_values.value_counts()
    duplicate_counts = counts[counts > 1]

    if df_identifier is not None and not duplicate_counts.empty:
        _write_duplicate_analysis_file(df, duplicate_counts, df_identifier)

    return int(duplicate_counts.size), int(duplicate_counts.sum())


def _log_primary_key_overlaps(
    results: Dict[Tuple[DatasetKind, DataSourceKind], pd.DataFrame],
) -> None:
    for first_combo, second_combo in OVERLAP_COMPARISONS:
        first_df = results.get(first_combo)
        second_df = results.get(second_combo)
        if first_df is None or second_df is None:
            logger.warning(
                "Missing data for overlap comparison between {}/{} and {}/{}.",
                first_combo[0].value,
                first_combo[1].value,
                second_combo[0].value,
                second_combo[1].value,
            )
            continue

        first_keys = set(first_df[COL_PRIMARY_KEY].dropna().unique())
        second_keys = set(second_df[COL_PRIMARY_KEY].dropna().unique())
        overlap_keys = first_keys & second_keys
        overlap_count = len(overlap_keys)
        pct_of_first_in_second = (
            overlap_count / len(first_keys) * 100 if first_keys else 0.0
        )
        pct_of_second_in_first = (
            overlap_count / len(second_keys) * 100 if second_keys else 0.0
        )
        logger.info(
            "Primary key overlap between {}/{} and {}/{} -> {} intersecting keys ({} vs {}).",
            first_combo[0].value,
            first_combo[1].value,
            second_combo[0].value,
            second_combo[1].value,
            overlap_count,
            len(first_keys),
            len(second_keys),
        )
        logger.info(
            "Primary keys from {}/{} present in {}/{}: {:.2f}%",
            first_combo[0].value,
            first_combo[1].value,
            second_combo[0].value,
            second_combo[1].value,
            pct_of_first_in_second,
        )
        logger.info(
            "Primary keys from {}/{} present in {}/{}: {:.2f}%",
            second_combo[0].value,
            second_combo[1].value,
            first_combo[0].value,
            first_combo[1].value,
            pct_of_second_in_first,
        )


if __name__ == "__main__":  # pragma: no cover - convenience for manual runs
    primary_key_results = run_primary_key_generation_checks()
    _log_primary_key_overlaps(primary_key_results)
