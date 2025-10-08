from typing import Dict, Type

from .base import BaseDeterministicFlow
from .summarize_business_partner_flow import SummarizeBusinessPartnerFlow

# A registry mapping flow names to their corresponding implementation classes.
DETERMINISTIC_FLOWS: Dict[str, Type[BaseDeterministicFlow]] = {
    # Use the proper flow that returns structured data
    "summarize_business_partner": SummarizeBusinessPartnerFlow,
}
