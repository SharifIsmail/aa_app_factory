"""Data-Preparation File Mapping
================================
This module acts as a *lookup table* for domain experts who know the original
Excel workbooks inside out but do **not** want to read Python source code.

For each Excel file that you hand over to the system we list – in plain
language – which additional data files are created further down the pipeline
and why they exist.

You can import the dictionary ``FILE_CREATION_MAP`` from this module or simply
open the file in a text editor to read the explanations.
"""

# The key is the original Excel workbook.
# Each value is a dictionary with two keys:
#   1. "direct_output" – the immediate parquet file that results from a straight
#      conversion of the Excel workbook (no content changes, only the file
#      format is switched for faster processing).
#   2. "downstream_outputs" – parquet files that are *derived* from the direct
#      output in later processing steps, together with a friendly explanation
#      of what each file represents.

CONCRETE_FILE_NAME = "Konkrete_Risiken.xlsx"
BRUTTO_FILE_NAME = "Brutto_Datei.xlsx"
RESOURCE_RISKS_FILE_NAME = "Rohstoffrisiken.xlsx"


FILE_CREATION_MAP: dict[str, dict[str, list[str] | str]] = {
    BRUTTO_FILE_NAME: {
        "direct_output": "brutto_file.parquet",
        "downstream_outputs": [
            f"transactions.parquet – every row from *Brutto-Risiken* and *Konkrete Risiken* combined with the rows from {CONCRETE_FILE_NAME} . Think of it as the full transaction log.",
            "business_partners.parquet – the same data, but bundled by business partner (one row per partner) plus extra columns that show the *highest* risk observed for that partner.",
            "risk_per_business_partner.parquet – pivoted view of the above: here each business partner is listed multiple times, once per risk type and supplier tier, making it easy to plot risk heatmaps.",
            "risk_per_branch.parquet – risk overview per industry branch (detailed sector) and country, useful for seeing which industries and countries are most at risk.",
        ],
    },
    CONCRETE_FILE_NAME: {
        "direct_output": "concrete_file.parquet",
        "downstream_outputs": [
            f"transactions.parquet – combined with {BRUTTO_FILE_NAME} as described above.",
            "business_partners.parquet – aggregated view per business partner.",
            "risk_per_business_partner.parquet – long-format risk table per partner.",
            "risk_per_branch.parquet – branch- and country-level risk summary.",
        ],
    },
    RESOURCE_RISKS_FILE_NAME: {
        "direct_output": "resource_risks.parquet",
        "downstream_outputs": [
            "resource_risks_processed.parquet – identical rows, but the column “Durchschnittliches Rohstoffrisiko …” is renamed to simply “Rohstoffname” so that charts and filters look tidy.",
        ],
    },
}
