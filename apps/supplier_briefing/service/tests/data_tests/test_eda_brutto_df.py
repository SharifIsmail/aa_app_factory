import pandas as pd

from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_FINEST_PRODUCT_LEVEL,
)
from service.eda.brutto_df import analyze_non_constant_columns


def test_analyze_non_constant_columns_print_dataframe() -> None:
    test_data = pd.DataFrame(
        {
            COL_BUSINESS_PARTNER_ID: ["BP001", "BP001", "BP001", "BP002", "BP002"],
            COL_FINEST_PRODUCT_LEVEL: [
                "Product_A",
                "Product_A",
                "Product_A",
                "Product_B",
                "Product_B",
            ],
            "price": [
                10.0,
                15.0,
                20.0,
                100.0,
                150.0,
            ],  # Non-constant for each combination
            "supplier_rating": ["A", "B", "A", "Excellent", "Good"],  # Non-constant
            "constant_field": [
                "SAME",
                "SAME",
                "SAME",
                "FIXED",
                "FIXED",
            ],  # Constant within each group
            "description": [
                "Desc1",
                "Desc2",
                "Desc3",
                "Desc_X",
                "Desc_Y",
            ],  # Non-constant
        }
    )

    result_df = analyze_non_constant_columns(test_data, "BP001", "Product_A")

    assert "constant_field" not in result_df.columns, (
        "Constant column should be excluded"
    )
    assert "price" in result_df.columns, "price column should be included"
    assert "supplier_rating" in result_df.columns, (
        "supplier_rating column should be included"
    )
    assert "description" in result_df.columns, "description column should be included"

    result_df_2 = analyze_non_constant_columns(test_data, "BP002", "Product_B")
    assert "price" in result_df_2.columns, "price column should be included"
    assert "supplier_rating" in result_df_2.columns, (
        "supplier_rating column should be included"
    )
    assert "description" in result_df_2.columns, "description column should be included"
    assert "constant_field" not in result_df_2.columns, (
        "constant_field should be excluded"
    )
