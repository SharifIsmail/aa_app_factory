from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_BRUTTO_PRIORISIERUNG,
    COL_DATA_SOURCE,
    COL_GROUPING_FACHBEREICH,
    COL_KONKRETE_PRIORISIERUNG,
    COL_NETTO_PRIORISIERUNG,
    COL_REVENUE_TOTAL,
    COL_SCHWARZ_GROUP_FLAG,
    COL_SCHWARZBESCHAFFUNG,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.data_loading import load_dataset_from_path


class BusinessPartnerPriorityMatrixTool(Tool):
    """
    Tool for analyzing business partner distribution across priority levels grouped by Fachbereichsebene or Warentyp.

    This tool creates cross-tabulation matrices showing how business partners are distributed
    across different priority levels, grouped by functional areas (Fachbereichsebene) or
    product types (Warentyp based on Datenquelle / Datenherkunft) after applying specific filters.
    """

    name = "get_bp_prio_matrix_filtered"

    inputs = {
        "priority_type": {
            "type": "string",
            "description": "The type of priority to analyze ('Netto', 'Konkrete', 'Brutto'). "
            "If not specified, will default to 'Konkrete' priority type.",
            "nullable": True,
        },
        "group_by": {
            "type": "string",
            "description": f"Column to group analysis by. Options: '{COL_GROUPING_FACHBEREICH}' "
            f"for functional areas or '{COL_DATA_SOURCE}' for product types. "
            f"Defaults to '{COL_GROUPING_FACHBEREICH}'.",
            "nullable": True,
        },
    }

    output_type = "any"

    description = (
        "This tool first applies **very** specific filters (revenue threshold, exclusion of Schwarzbeschaffung "
        "partners, and exclusion of Schwarz group companies) and then returns a distribution matrix of business partners across priority levels "
        "grouped by either Fachbereichsebene (functional areas/departments) or Warentyp (product types) to the result obtained from filtering. "
        "Returns a pandas.DataFrame showing the cross-tabulation of groups vs priority levels after filtering. Note that not all business partners are counted, but only those that remain after the filters are applied. "
        "DO NOT USE THIS TOOL to get business partner counts per department, because it applies specific filters first. "
        "Usage examples: "
        "matrix_df = get_bp_prio_matrix_filtered('Konkrete') # returns filtered count matrix for concrete priority grouped by departments "
        "warentyp_matrix = get_bp_prio_matrix_filtered('Konkrete', group_by='Datenquelle / Datenherkunft') # group by product types "
    )

    def __init__(
        self,
        business_partner_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.file_path = business_partner_file
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log

        # Define valid grouping columns
        self.valid_grouping_columns = [COL_GROUPING_FACHBEREICH, COL_DATA_SOURCE]

        # Default grouping column
        self.default_group_by = COL_GROUPING_FACHBEREICH

        self.priority_columns = {
            "Netto": COL_NETTO_PRIORISIERUNG,
            "Konkrete": COL_KONKRETE_PRIORISIERUNG,
            "Brutto": COL_BRUTTO_PRIORISIERUNG,
        }

        # Business logic columns
        self.filters_columns = {
            "revenue": COL_REVENUE_TOTAL,
            "schwarzbeschaffung": COL_SCHWARZBESCHAFFUNG,
            "schwarz_group": COL_SCHWARZ_GROUP_FLAG,
        }

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist in the dataframe."""
        missing_cols = []

        # Check grouping columns
        for col_name in self.valid_grouping_columns:
            if col_name not in df.columns:
                missing_cols.append(f"Grouping column: {col_name}")

        for priority_type, col_name in self.priority_columns.items():
            if col_name not in df.columns:
                missing_cols.append(f"{priority_type}: {col_name}")

        # Check for business logic columns (for warnings only)
        missing_filters_cols = []
        for filter_type, col_name in self.filters_columns.items():
            if col_name not in df.columns:
                missing_filters_cols.append(f"{filter_type}: {col_name}")

        if missing_cols:
            logger.warning(f"Missing priority/grouping columns: {missing_cols}")
            # Try to find similar column names
            available_cols = [
                col
                for col in df.columns
                if "priorisierung" in col.lower()
                or "fachbereich" in col.lower()
                or "datenquell" in col.lower()
            ]
            logger.info(f"Available similar columns: {available_cols}")

        if missing_filters_cols:
            logger.warning(
                f"Missing TBAF-90 filter columns (filters will be skipped): {missing_filters_cols}"
            )

    def _split_comma_separated_rows(
        self, df: pd.DataFrame, column_name: str
    ) -> pd.DataFrame:
        """
        Split rows where the specified column has comma-separated values into multiple rows.

        Args:
            df: DataFrame to process
            column_name: Name of the column to split

        Returns:
            DataFrame with comma-separated values split into separate rows
        """
        if column_name not in df.columns:
            logger.warning(f"Column '{column_name}' not found in DataFrame")
            return df

        # Create a copy of the DataFrame
        df_expanded = df.copy()

        # Find rows with comma-separated values
        comma_mask = df_expanded[column_name].astype(str).str.contains(",", na=False)

        if comma_mask.sum() == 0:
            logger.info("No comma-separated values found.")
            return df_expanded

        logger.info(
            f"Found {comma_mask.sum()} rows with comma-separated values to split..."
        )

        # Split the comma-separated values and explode into multiple rows
        df_expanded[column_name] = df_expanded[column_name].astype(str).str.split(",")
        df_expanded = df_expanded.explode(column_name)

        # Clean up the values (remove leading/trailing whitespace)
        df_expanded[column_name] = df_expanded[column_name].str.strip()

        # Reset index
        df_expanded = df_expanded.reset_index(drop=True)

        logger.info(f"Original DataFrame shape: {df.shape}")
        logger.info(f"Expanded DataFrame shape: {df_expanded.shape}")
        logger.info(f"Added {df_expanded.shape[0] - df.shape[0]} new rows")

        return df_expanded

    def _apply_filters(
        self, df: pd.DataFrame, min_revenue_threshold: float = 10000.0
    ) -> pd.DataFrame:
        """
        Apply business logic filters to the dataframe.

        Filtering conditions:
        1. Only business partners with revenue >= threshold
        2. Exclude partners negotiated by Schwarzbeschaffung
        3. Exclude partners belonging to Schwarz group
        """
        df_filtered = df.copy()
        initial_count = len(df_filtered)

        logger.info(
            f"Applying TBAF-90 filters. Initial dataset: {initial_count} business partners"
        )

        # CONDITION 1: Revenue threshold filter
        revenue_col = self.filters_columns.get("revenue")
        if revenue_col and revenue_col in df_filtered.columns:
            logger.info(
                f"CONDITION 1: Filtering for revenue >= {min_revenue_threshold:,.0f} €"
            )

            clean_revenue_col = revenue_col + "_clean"

            # Validate that the clean revenue column exists
            if clean_revenue_col not in df_filtered.columns:
                raise ValueError(
                    f"Revenue filtering failed: Clean revenue column '{clean_revenue_col}' not found in dataset. "
                    f"Available columns: {list(df_filtered.columns)}"
                )

            before_revenue_filter = len(df_filtered)

            # Apply the revenue filter with proper error handling
            df_filtered = df_filtered[
                df_filtered[clean_revenue_col] >= min_revenue_threshold
            ]

            logger.info(
                f"Revenue filter: {before_revenue_filter} -> {len(df_filtered)} partners"
            )
        else:
            raise ValueError(
                f"Revenue filtering failed: Required revenue column '{revenue_col}' not found in dataset. "
                f"Available columns: {list(df_filtered.columns)}"
            )

        # CONDITION 2: Exclude Schwarzbeschaffung partners
        schwarzbeschaffung_col = self.filters_columns.get("schwarzbeschaffung")
        if schwarzbeschaffung_col and schwarzbeschaffung_col in df_filtered.columns:
            logger.info(
                "CONDITION 2: Excluding partners negotiated by Schwarzbeschaffung"
            )

            # Define positive values indicating Schwarzbeschaffung
            # @ToDo: optimize this to be case-insensitive
            schwarzbeschaffung_positive_values = ["x"]

            before_schwarz_filter = len(df_filtered)

            # Filter using explicit boolean indexing
            mask = ~df_filtered.loc[:, schwarzbeschaffung_col].isin(
                schwarzbeschaffung_positive_values
            )
            df_filtered = df_filtered.loc[mask].copy()
            logger.info(
                f"Schwarzbeschaffung filter: {before_schwarz_filter} -> {len(df_filtered)} partners"
            )
        else:
            logger.warning(
                f"Schwarzbeschaffung column '{schwarzbeschaffung_col}' not found, skipping filter"
            )

        # CONDITION 3: Exclude Schwarz group partners
        schwarz_group_col = self.filters_columns.get("schwarz_group")
        if schwarz_group_col and schwarz_group_col in df_filtered.columns:
            logger.info("CONDITION 3: Excluding partners belonging to Schwarz group")

            # Use same positive values as Schwarzbeschaffung
            # @ToDo: optimize this to be case-insensitive
            schwarz_group_positive_values = ["X"]

            before_group_filter = len(df_filtered)

            # Filter using explicit boolean indexing
            mask = ~df_filtered.loc[:, schwarz_group_col].isin(
                schwarz_group_positive_values
            )
            df_filtered = df_filtered.loc[mask].copy()
            logger.info(
                f"Schwarz group filter: {before_group_filter} -> {len(df_filtered)} partners"
            )
        else:
            logger.warning(
                f"Schwarz group column '{schwarz_group_col}' not found, skipping filter"
            )

        final_count = len(df_filtered)
        filter_reduction = (
            ((initial_count - final_count) / initial_count * 100)
            if initial_count > 0
            else 0
        )

        logger.info(
            f"TBAF-90 filters applied: {initial_count} -> {final_count} partners "
            f"({filter_reduction:.1f}% reduction)"
        )

        # Ensure return type is DataFrame
        return pd.DataFrame(df_filtered)

    def _create_priority_matrix(
        self,
        df: pd.DataFrame,
        priority_type: str,
        group_by: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Create the business partner priority distribution matrix with specific filters.
        """
        # Get the priority column for the specified type
        priority_col = self.priority_columns.get(priority_type)
        if not priority_col or priority_col not in df.columns:
            available_types = [
                k for k, v in self.priority_columns.items() if v in df.columns
            ]
            raise ValueError(
                f"Priority type '{priority_type}' not available. "
                f"Available types: {available_types}"
            )

        # @ToDo: remove and cleanup this code
        # Determine grouping column
        if not group_by:
            group_by = self.default_group_by

        if group_by not in self.valid_grouping_columns or group_by not in df.columns:
            available_groups = [
                col for col in self.valid_grouping_columns if col in df.columns
            ]
            raise ValueError(
                f"Grouping column '{group_by}' not found in data. "
                f"Available options: {available_groups}"
            )

        # Apply business logic filters
        df = self._apply_filters(df)

        # Split comma-separated values in the grouping column into separate rows
        logger.info(f"Splitting comma-separated values in {group_by} column...")
        df = self._split_comma_separated_rows(df, group_by)

        # Filter out null values for analysis columns
        valid_data = df.dropna(subset=[group_by, priority_col])

        if valid_data.empty:
            raise ValueError(
                "No valid data found after applying filters and removing null values"
            )

        logger.info(f"Using concrete prioritization: '{priority_col}'")
        logger.info(f"Grouping by: '{group_by}'")
        logger.info(f"Final analysis dataset: {len(valid_data)} business partners")
        logger.info(f"Unique groups: {valid_data[group_by].nunique()}")
        logger.info(f"Unique priority levels: {valid_data[priority_col].nunique()}")

        # Create cross-tabulation
        matrix = pd.crosstab(
            valid_data[group_by],
            valid_data[priority_col],
            margins=True,
            margins_name="Gesamtergebnis",
        )

        return matrix

    def forward(
        self,
        priority_type: Optional[str] = None,
        group_by: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Core tool logic without tracing.
        """
        tool_log = ToolLog(
            tool_name=self.name,
            description="Generate business partner priority distribution matrix",
            params={
                "priority_type": priority_type,
                "group_by": group_by,
            },
        )
        self.work_log.tool_logs.append(tool_log)

        try:
            # Default values
            if not priority_type:
                priority_type = "Konkrete"
            if not group_by:
                group_by = self.default_group_by

            # Validate priority type
            if priority_type not in self.priority_columns:
                raise ValueError(
                    f"Invalid priority type '{priority_type}'. "
                    f"Valid options: {list(self.priority_columns.keys())}"
                )

            # Validate group_by
            if group_by not in self.valid_grouping_columns:
                raise ValueError(
                    f"Invalid group_by '{group_by}'. "
                    f"Valid options: {self.valid_grouping_columns}"
                )

            # Load dataset lazily and validate
            df = load_dataset_from_path(self.file_path)
            self._validate_columns(df)

            matrix = self._create_priority_matrix(
                df=df,
                priority_type=priority_type,
                group_by=group_by,
            )

            logger.info(
                f"Successfully created business partner priority matrix for {priority_type} "
                f"priority grouped by {group_by} with {len(matrix) - 1} groups and {len(matrix.columns) - 1} priority levels"
            )

            return matrix

        except Exception as e:
            logger.error(f"Error in {self.name}: {str(e)}")
            tool_log.result = f"Error: {str(e)}"
            raise
