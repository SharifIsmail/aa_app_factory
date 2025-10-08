import pandas as pd

from service.agent_core.constants import DATA_SOURCE_HW, DATA_SOURCE_NHW
from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_ARTIKELFAMILIE,
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_DATA_SOURCE,
    COL_ESTELL_SEKTOR_DETAILLIERT_RAW,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_ESTELL_SEKTOR_GROB_RAW,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_ID_ARTICLE_NAME,
    COL_ID_WG_EBENE_8_SACHKONTO,
    COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
    COL_MARKENTYP_HANDELSWARE,
    COL_PROCUREMENT_UNIT,
    COL_REVENUE_TOTAL,
    COL_WG_EBENE_7_KER_POSITION,
    EMPTY_VALUES,
)
from service.agent_core.data_management.paths import get_data_dir
from service.data_loading import load_dataset_from_path
from service.data_preparation import (
    BRUTTO_FILE_CLEANED_PARQUET,
    BRUTTO_FILE_PARQUET,
    CONCRETE_FILE_CLEANED_PARQUET,
    CONCRETE_FILE_PARQUET,
    ColumnProcessor,
    assert_column_depends_on_other_column,
    clean_business_partner_id_columns,
    clean_business_partner_name,
    clean_original_dataframes,
    create_derived_dataframes,
    split_and_merge_brutto_and_concrete_along_data_source_column,
    split_dataframe_by_data_source,
)


def test_clean_business_partner_name() -> None:
    # create test dataframes with non-unique business partner names for the same ID
    df_1 = pd.DataFrame(
        {
            COL_BUSINESS_PARTNER_ID: ["1", "1"],
            COL_BUSINESS_PARTNER_NAME: ["Name 1A", "Name 1B"],
        }
    )
    df_2 = pd.DataFrame(
        {
            COL_BUSINESS_PARTNER_ID: ["1", "1"],
            COL_BUSINESS_PARTNER_NAME: ["Name 1A", "Name 1C"],
        }
    )

    output_dfs = clean_business_partner_name([df_1, df_2])
    for df in output_dfs:
        assert_column_depends_on_other_column(df, COL_BUSINESS_PARTNER_NAME)


def test_create_derived_dataframes_runnable() -> None:
    create_derived_dataframes(
        load_dataset_from_path(get_data_dir() / BRUTTO_FILE_CLEANED_PARQUET),
        load_dataset_from_path(get_data_dir() / CONCRETE_FILE_CLEANED_PARQUET),
    )


def test_clean_original_dataframes() -> None:
    brutto_df_cleaned, concrete_df_cleaned = clean_original_dataframes(
        load_dataset_from_path(get_data_dir() / BRUTTO_FILE_PARQUET),
        load_dataset_from_path(get_data_dir() / CONCRETE_FILE_PARQUET),
    )
    for df in [brutto_df_cleaned, concrete_df_cleaned]:
        assert COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED in df.columns
        assert COL_ESTELL_SEKTOR_GROB_RENAMED in df.columns
        assert COL_ESTELL_SEKTOR_DETAILLIERT_RAW not in df.columns
        assert COL_ESTELL_SEKTOR_GROB_RAW not in df.columns


def test_column_processor_extract_raw_parts_from_value() -> None:
    processor = ColumnProcessor(separator="/")

    # Test normal case - should return raw parts without cleaning
    assert processor._extract_raw_parts_from_value("foo1 / bar1") == ["foo1 ", " bar1"]

    # Test with extra whitespace - should preserve whitespace
    assert processor._extract_raw_parts_from_value("  foo1  /  bar1  ") == [
        "  foo1  ",
        "  bar1  ",
    ]

    # Test empty parts are NOT filtered out
    assert processor._extract_raw_parts_from_value("foo1 / / bar1") == [
        "foo1 ",
        " ",
        " bar1",
    ]

    # Test single value
    assert processor._extract_raw_parts_from_value("foo1") == ["foo1"]

    # Test null/NaN values
    assert processor._extract_raw_parts_from_value(None) == []
    assert processor._extract_raw_parts_from_value("N.A.") == []
    assert processor._extract_raw_parts_from_value("nan") == []


def test_column_processor_clean_parts() -> None:
    processor = ColumnProcessor(separator="/")

    # Test normal case
    assert processor._clean_parts(["foo1 ", " bar1"]) == ["foo1", "bar1"]

    # Test with extra whitespace
    assert processor._clean_parts(["  foo1  ", "  bar1  "]) == ["foo1", "bar1"]

    # Test empty parts are filtered out
    assert processor._clean_parts(["foo1 ", " ", " bar1"]) == ["foo1", "bar1"]

    # Test single value
    assert processor._clean_parts(["foo1"]) == ["foo1"]

    # Test empty list
    assert processor._clean_parts([]) == []

    # Test only empty/whitespace parts
    assert processor._clean_parts(["", "  ", "\t"]) == []


def test_column_processor_extract_parts_from_value() -> None:
    processor = ColumnProcessor(separator="/")

    # Test normal case
    assert processor._extract_and_clean_parts_from_value("foo1 / bar1") == [
        "FOO1",
        "BAR1",
    ]

    # Test with extra whitespace
    assert processor._extract_and_clean_parts_from_value("  foo1  /  bar1  ") == [
        "FOO1",
        "BAR1",
    ]

    # Test empty parts are filtered out
    assert processor._extract_and_clean_parts_from_value("foo1 / / bar1") == [
        "FOO1",
        "BAR1",
    ]

    # Test single value
    assert processor._extract_and_clean_parts_from_value("foo1") == ["FOO1"]

    # Test null/NaN values
    assert processor._extract_and_clean_parts_from_value(None) == []
    assert processor._extract_and_clean_parts_from_value("N.A.") == []
    assert processor._extract_and_clean_parts_from_value("nan") == []


def test_column_processor_sort_single_value() -> None:
    processor = ColumnProcessor(separator="/")

    # Test normal case with sorting
    assert processor.sort_single_value("foo1 / bar1") == "BAR1/FOO1"

    # Test with whitespace
    assert processor.sort_single_value("  foo1  / bar1   ") == "BAR1/FOO1"

    # Test single value
    assert processor.sort_single_value("foo1") == "FOO1"

    # Test null/NaN values return empty string
    assert processor.sort_single_value(None) == ""
    assert processor.sort_single_value("N.A.") == ""
    assert processor.sort_single_value("nan") == ""


def test_column_processor_sort_separated_column() -> None:
    processor = ColumnProcessor(separator="/")

    # Test DataFrame processing
    df = pd.DataFrame({"materials": ["bar1 / foo1", "foo2/baz1", None, "N.A."]})

    result_df = processor.sort_separated_column(df, "materials")
    expected_values = ["BAR1/FOO1", "BAZ1/FOO2", "", ""]
    assert result_df["materials"].tolist() == expected_values

    # Test with column not found
    try:
        processor.sort_separated_column(df, "nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found in dataframe" in str(e)


def test_clean_business_partner_id_columns(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame
) -> None:
    for df in [brutto_df, concrete_df]:
        df_cleaned = clean_business_partner_id_columns(df)
        for empty_value in EMPTY_VALUES:
            assert empty_value not in df_cleaned[COL_BUSINESS_PARTNER_ID]
            if isinstance(empty_value, str):
                assert empty_value.lower() not in df_cleaned[COL_BUSINESS_PARTNER_ID]
                assert empty_value.upper() not in df_cleaned[COL_BUSINESS_PARTNER_ID]


def test_split_dataframe_by_data_source() -> None:
    # Create test dataframe with both HW and NHW data sources
    df = pd.DataFrame(
        {
            COL_DATA_SOURCE: [
                DATA_SOURCE_HW,
                DATA_SOURCE_HW,
                DATA_SOURCE_NHW,
                DATA_SOURCE_NHW,
                DATA_SOURCE_NHW,
            ],
            COL_BUSINESS_PARTNER_ID: ["1", "2", "3", "4", "5"],
            "some_value": [10, 20, 30, 40, 50],
        }
    )

    # Call the split function
    df_hw, df_nhw = split_dataframe_by_data_source(df)

    # Assert correct number of rows in each split
    assert len(df_hw) == 2, f"Expected 2 HW rows, got {len(df_hw)}"
    assert len(df_nhw) == 3, f"Expected 3 NHW rows, got {len(df_nhw)}"

    # Assert total rows match
    assert len(df_hw) + len(df_nhw) == len(df), "Total rows don't match original"

    # Assert correct business partner IDs in each split
    assert set(df_hw[COL_BUSINESS_PARTNER_ID]) == {"1", "2"}
    assert set(df_nhw[COL_BUSINESS_PARTNER_ID]) == {"3", "4", "5"}

    # Assert data values are preserved
    assert df_hw["some_value"].tolist() == [10, 20]
    assert df_nhw["some_value"].tolist() == [30, 40, 50]


def test_split_and_merge_brutto_and_concrete_along_data_source_column() -> None:
    # Create brutto dataframe with HW and NHW data
    brutto_df = pd.DataFrame(
        {
            COL_DATA_SOURCE: [DATA_SOURCE_HW, DATA_SOURCE_HW, DATA_SOURCE_NHW],
            COL_BUSINESS_PARTNER_ID: ["BP1", "BP2", "BP3"],
            COL_PROCUREMENT_UNIT: ["Unit1", "Unit2", "Unit3"],
            COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED: ["Sector1", "Sector2", "Sector3"],
            # HW-specific columns
            COL_REVENUE_TOTAL: ["1000", "2000", "3000"],
            COL_MARKENTYP_HANDELSWARE: ["M", "EM", "HM"],
            COL_ARTIKELFAMILIE: ["Family1", "Family2", "Family3"],
            COL_ARTICLE_NAME: ["Article1", "Article2", "Article3"],
            COL_ID_ARTICLE_NAME: ["A1", "A2", "A3"],
            # NHW-specific columns
            COL_WG_EBENE_7_KER_POSITION: ["KER1", "KER2", "KER3"],
            COL_ID_WG_EBENE_8_SACHKONTO: ["SK1", "SK2", "SK3"],
            COL_ID_WG_EBENE_9_KOSTENKATEGORIE: ["KK1", "KK2", "KK3"],
            "brutto_specific_column": ["B1", "B2", "B3"],
        }
    )

    # Create concrete dataframe with HW and NHW data (overlapping keys with brutto)
    concrete_df = pd.DataFrame(
        {
            COL_DATA_SOURCE: [DATA_SOURCE_HW, DATA_SOURCE_NHW],
            COL_BUSINESS_PARTNER_ID: ["BP1", "BP3"],
            COL_PROCUREMENT_UNIT: ["Unit1", "Unit3"],
            COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED: ["Sector1", "Sector3"],
            # HW-specific columns
            COL_REVENUE_TOTAL: ["1000", "3000"],
            COL_MARKENTYP_HANDELSWARE: ["M", "HM"],
            COL_ARTIKELFAMILIE: ["Family1", "Family3"],
            COL_ARTICLE_NAME: ["Article1", "Article3"],
            COL_ID_ARTICLE_NAME: ["A1", "A3"],
            # NHW-specific columns
            COL_WG_EBENE_7_KER_POSITION: ["KER1", "KER3"],
            COL_ID_WG_EBENE_8_SACHKONTO: ["SK1", "SK3"],
            COL_ID_WG_EBENE_9_KOSTENKATEGORIE: ["KK1", "KK3"],
            "concrete_specific_column": ["C1", "C3"],
        }
    )

    # Call the function
    merged_hw, merged_nhw = (
        split_and_merge_brutto_and_concrete_along_data_source_column(
            brutto_df, concrete_df, create_conflicts_files=False
        )
    )

    # Verify HW merge results
    assert len(merged_hw) == 2, f"Expected 2 HW rows, got {len(merged_hw)}"
    assert set(merged_hw[COL_BUSINESS_PARTNER_ID]) == {"BP1", "BP2"}

    # Verify NHW merge results
    assert len(merged_nhw) == 1, f"Expected 1 NHW row, got {len(merged_nhw)}"
    assert set(merged_nhw[COL_BUSINESS_PARTNER_ID]) == {"BP3"}

    # Verify columns from both brutto and concrete are present in merged HW
    assert "brutto_specific_column" in merged_hw.columns
    assert "concrete_specific_column" in merged_hw.columns

    # Verify columns from both brutto and concrete are present in merged NHW
    assert "brutto_specific_column" in merged_nhw.columns
    assert "concrete_specific_column" in merged_nhw.columns
