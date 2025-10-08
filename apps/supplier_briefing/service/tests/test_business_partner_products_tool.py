import random
from uuid import uuid4

import pandas as pd
import pytest

from service.agent_core.data_management.columns import COL_BUSINESS_PARTNER_ID
from service.agent_core.model_tools_manager import DATA_DIR
from service.agent_core.tools.business_partner_products_tool import (
    BusinessPartnerProductsTool,
)
from service.agent_core.work_log_manager import create_work_log
from service.data_loading import load_dataset_from_path
from service.data_preparation import TRANSACTIONS_PARQUET


@pytest.fixture
def business_partner_products_tool() -> BusinessPartnerProductsTool:
    execution_id = str(uuid4())
    work_log = create_work_log(execution_id)
    transaction_file = DATA_DIR / TRANSACTIONS_PARQUET

    return BusinessPartnerProductsTool(
        transaction_file=transaction_file,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )


class TestBusinessPartnerProductsTool:
    def test_forward_correct_return_type(
        self, business_partner_products_tool: BusinessPartnerProductsTool
    ) -> None:
        transaction_df = load_dataset_from_path(DATA_DIR / TRANSACTIONS_PARQUET)
        for business_partner_id in sorted(
            random.sample(list(set(transaction_df[COL_BUSINESS_PARTNER_ID])), 100)
        ):
            df = business_partner_products_tool.forward(
                business_partner_id=business_partner_id
            )
            assert isinstance(df, pd.DataFrame)
