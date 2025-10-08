"""Quick action data fetchers mapping."""

from enum import Enum

from service.quick_actions.abstract_fetcher import BaseQuickActionDataFetcher
from service.quick_actions.models import QuickAction
from service.quick_actions.summarize_business_partner import (
    SummarizeBusinessPartnerDataFetcher,
)


class QuickActionFetcher(Enum):
    """Maps quick actions to their data fetcher classes."""

    SUMMARIZE_BUSINESS_PARTNER = SummarizeBusinessPartnerDataFetcher

    @classmethod
    def get_fetcher(cls, quick_action: QuickAction) -> BaseQuickActionDataFetcher:
        """Get a data fetcher instance for a given quick action."""
        fetcher_class = cls[quick_action.name].value
        return fetcher_class()
