import numpy as np
import pandas as pd


def generate_pandas_preview(
    df: pd.DataFrame | pd.Series, max_rows: int = 10, max_cols: int = 20
) -> str:
    """
    Generate an enhanced, LLM-friendly preview of a pandas DataFrame or Series.

    Args:
        df: pandas DataFrame or Series
        max_rows: Maximum number of rows to display
        max_cols: Maximum number of columns to display

    Returns:
        String with enhanced preview information
    """

    # Constants
    LARGE_SIZE_THRESHOLD = 100_000

    if df is None:
        return "Error: No data available"

    try:
        # Handle Series
        if isinstance(df, pd.Series):
            series_length = len(df)
            use_sampling = series_length > LARGE_SIZE_THRESHOLD

            preview_lines = [
                f"📊 SERIES PREVIEW",
                f"Shape: ({series_length:,},)",
                f"Name: {df.name or 'Unnamed'}",
                f"Data Type: {df.dtype}",
                "",
                "Sample Values:",
            ]

            if use_sampling:
                sample_indices = np.random.choice(
                    series_length, max_rows, replace=False
                )
                sample_indices = np.sort(sample_indices)
                for idx in sample_indices:
                    preview_lines.append(f"  [{idx}]: {df.iloc[idx]}")
                preview_lines.append(f"  (sampled from {series_length:,} total values)")
            else:
                sample_data = df.head(max_rows)
                for idx, value in sample_data.items():
                    preview_lines.append(f"  [{idx}]: {value}")
                if series_length > max_rows:
                    preview_lines.append(
                        f"  ... and {series_length - max_rows:,} more values"
                    )

            return "\n".join(preview_lines)

        # Handle DataFrame
        elif isinstance(df, pd.DataFrame):
            total_rows, total_cols = df.shape
            use_sampling = total_rows > LARGE_SIZE_THRESHOLD

            preview_lines = [
                f"📊 DATAFRAME PREVIEW",
                f"Shape: ({total_rows:,}, {total_cols})",
            ]

            preview_lines.append("")

            # Show columns
            cols_to_show = df.columns[:max_cols].tolist()
            preview_lines.append(f"Columns ({total_cols}):")
            for i, col in enumerate(cols_to_show):
                col_dtype = str(df[col].dtype)
                preview_lines.append(f"  {i + 1}. '{col}' ({col_dtype})")

            if total_cols > max_cols:
                preview_lines.append(f"  ... and {total_cols - max_cols} more columns")

            preview_lines.append("")
            preview_lines.append("Sample Data:")

            # Sample data
            if use_sampling:
                sample_indices = np.random.choice(total_rows, max_rows, replace=False)
                sample_indices = np.sort(sample_indices)
                sample_df = df.iloc[sample_indices, :max_cols]
                preview_lines.append(f"  (showing {max_rows} random rows)")
            else:
                sample_df = df.iloc[:max_rows, :max_cols]

            sample_str = sample_df.to_string(
                max_rows=max_rows,
                max_cols=max_cols,
                show_dimensions=False,
                max_colwidth=25,
            )

            indented_sample = "\n".join(f"  {line}" for line in sample_str.split("\n"))
            preview_lines.append(indented_sample)

            # Add truncation info
            if total_rows > max_rows:
                preview_lines.append(f"  ... and {total_rows - max_rows:,} more rows")
            if total_cols > max_cols:
                preview_lines.append(f"  ... and {total_cols - max_cols} more columns")

            return "\n".join(preview_lines)

        else:
            return f"Unsupported data type: {type(df)}"

    except Exception as e:
        return f"Error generating preview: {str(e)}"
