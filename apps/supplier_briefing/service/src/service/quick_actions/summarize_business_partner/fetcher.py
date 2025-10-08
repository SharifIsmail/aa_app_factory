"""Business partner data fetcher implementation."""

from typing import List

from loguru import logger

from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
)
from service.agent_core.data_management.paths import get_data_dir
from service.data_loading import load_dataset_from_path
from service.data_preparation import BUSINESS_PARTNERS_PARQUET
from service.quick_actions.abstract_fetcher import (
    BaseQuickActionDataFetcher,
    QuickActionResponse,
)
from service.quick_actions.summarize_business_partner.models import (
    PartnerData,
    SummarizeBusinessPartnerParams,
)


class SummarizeBusinessPartnerDataFetcher(
    BaseQuickActionDataFetcher[PartnerData, SummarizeBusinessPartnerParams]
):
    """Data fetcher for summarize business partner quick action."""

    def __init__(self) -> None:
        """Initialize the fetcher with data file path."""
        self._data_dir = get_data_dir()
        self._file_path = self._data_dir / BUSINESS_PARTNERS_PARQUET

    def validate_filter_params(
        self, filter_params: SummarizeBusinessPartnerParams
    ) -> None:
        pass

    def fetch_data(
        self, filter_params: SummarizeBusinessPartnerParams
    ) -> QuickActionResponse[PartnerData]:
        """
        Fetch and filter business partner data.

        Args:
            filter_params: Filter criteria for summarize_business_partner flow.

        Returns:
            QuickActionResponse with partner data
        """
        try:
            self.validate_filter_params(filter_params)

            query = filter_params.query.lower().strip()
            limit = filter_params.limit

            logger.info(
                f"Fetching business partners with query='{query}', limit={limit}"
            )

            filtered_data: List[PartnerData] = self._load_and_filter_data(query, limit)

            logger.info(f"Found and returning {len(filtered_data)} partners")

            return QuickActionResponse[PartnerData](
                success=True,
                data=filtered_data,
                error=None,
            )

        except Exception as e:
            logger.error(f"Error fetching business partner data: {str(e)}")
            return QuickActionResponse[PartnerData](
                success=False,
                data=[],
                error="Failed to fetch business partner data",
            )

    def _load_and_filter_data(self, query: str, limit: int) -> List[PartnerData]:
        """
        Load and filter business partner data efficiently using pandas.

        Args:
            query: Search query (searches both ID and name)
            limit: Maximum number of results to return

        Returns:
            List of filtered PartnerData objects
        """
        if not self._file_path.exists():
            raise FileNotFoundError(
                f"Business partners file not found: {self._file_path}"
            )

        logger.info(f"Loading and filtering business partners from {self._file_path}")

        required_columns = [COL_BUSINESS_PARTNER_ID, COL_BUSINESS_PARTNER_NAME]

        df = load_dataset_from_path(self._file_path, columns=required_columns)

        df["id_str"] = df[COL_BUSINESS_PARTNER_ID].astype(str)
        df["name_str"] = df[COL_BUSINESS_PARTNER_NAME].astype(str)
        df["id_lower"] = df["id_str"].str.lower()
        df["name_lower"] = df["name_str"].str.lower()

        if query:
            query_lower = query.lower()
            mask = df["id_lower"].str.contains(query_lower, case=False, na=False) | df[
                "name_lower"
            ].str.contains(query_lower, case=False, na=False)
            df_filtered = df[mask]
        else:
            df_filtered = df

        df_limited = df_filtered.head(limit)
        partners = []
        for _, row in df_limited.iterrows():
            partner_data = PartnerData(id=row["id_str"], name=row["name_str"])
            partners.append(partner_data)

        logger.info(
            f"Filtered from {len(df)} to {len(df_filtered)} partners, returning {len(partners)}"
        )
        return partners
