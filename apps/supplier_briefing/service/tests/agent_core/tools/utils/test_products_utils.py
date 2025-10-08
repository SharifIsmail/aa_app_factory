from service.agent_core.model_tools_manager import DATA_DIR
from service.agent_core.tools.utils.products_utils import (
    get_business_partner_data_if_needed,
)
from service.data_loading import load_dataset_from_path
from service.data_preparation import TRANSACTIONS_PARQUET


def test_get_business_partner_data_if_needed_is_runnable() -> None:
    transactions_df = load_dataset_from_path(DATA_DIR / TRANSACTIONS_PARQUET)
    get_business_partner_data_if_needed(transactions_df)
