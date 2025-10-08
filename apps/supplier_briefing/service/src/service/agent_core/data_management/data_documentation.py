from enum import Enum
from functools import lru_cache
from pathlib import Path

from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_ARTIKELFAMILIE,
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_COUNTRY,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_FRUIT_VEG_GROUP,
    COL_GROUPING_FACHBEREICH,
    COL_HAUPTWARENGRUPPE,
    COL_KONKRETE_PRIORISIERUNG,
    COL_LAENDERHERKUENFTE,
    COL_NETTO_PRIORISIERUNG,
    COL_PLACE_OF_PRODUCTION_ID,
    COL_PLACE_OF_PRODUCTION_NAME,
    COL_PROCUREMENT_UNIT,
    COL_RELATIVE_PURCHASE_VALUE,
    COL_REVENUE_TOTAL,
    COL_RISIKOROHSTOFFE,
    COL_RISKIEST_RESOURCE,
    COL_ROHSTOFFNAME,
    COL_SCHWARZ_GROUP_FLAG,
    COL_SUPPLIED_UNIT,
    COL_UNTERWARENGRUPPE,
    COL_WG_EBENE_3_WGI,
    COL_WG_EBENE_7_KER_POSITION,
    COL_WG_EBENE_8_SACHKONTO,
    COL_WG_EBENE_9_KOSTENKATEGORIE,
)
from service.agent_core.data_management.paths import get_data_dir
from service.agent_core.data_management.transactions import Transactions
from service.data_loading import DataFile
from service.data_preparation import (
    BUSINESS_PARTNERS_PARQUET,
    RESOURCE_RISKS_PROCESSED_PARQUET,
    RISK_PER_BRANCH_PARQUET,
    RISK_PER_BUSINESS_PARTNER_PARQUET,
    TRANSACTIONS_PARQUET,
)


class DatasetName(Enum):
    BUSINESS_PARTNERS = BUSINESS_PARTNERS_PARQUET
    RISK_PER_BUSINESS_PARTNER = RISK_PER_BUSINESS_PARTNER_PARQUET
    RISK_PER_BRANCH = RISK_PER_BRANCH_PARQUET
    TRANSACTIONS = TRANSACTIONS_PARQUET
    RESOURCE_RISKS_PROCESSED = RESOURCE_RISKS_PROCESSED_PARQUET


class DataDocumentation:
    @classmethod
    def get_glossary(cls) -> str:
        return f"""Here is a glossary of abbreviations and terminology:
| Term | Meaning | English Translation |
|------|---------|---------------------|
| GP | Geschäftspartner (business partner) | Business partner |
| SBES | Schwarz Beschaffung | Schwarz Procurement |
| EK-Wert | Einkaufswert | Purchase value |
| estell | Input/Output model from "Systain" for risk and environment impact | Input/Output model from "Systain" for risk and environment impact |
| Brutto Risiko | von Systain auf Basis von Studien; "Allgemeine Risiken" branchen- oder landesspezifisch | Gross risk from Systain based on studies; "General risks" industry- or country-specific |
| HW | Handelsware | Trading goods/Merchandise |
| NHW | Nicht-Handelsware | Non-trading goods |
| M | Marke | Brand |
| EM | Eigenmarke | Private label/Own brand |
| HM | Handelsmarke | Trading brand |
| HWG | Hauptwarengruppe | Main product group |
| WGI | most likely “Warengruppen-Identifikator” | Product group identificator |
| UWG | Unterwarengruppe | Sub-product group |
| KER | most likely “Kostenarten-Erfassung”  | Cost type entry  |

# Products / Articles

Product and articles are often used as synonyms.
In German they may be called "Artikel" or "Produkte", in English, "products", "items" or "articles".

# Product Categories ("Warengruppen")

There are several "Ebenen" of product categories, from general to specific:

- **Ebene 1**: Main product category (Hauptwarengruppe): Rough sector that product belongs to
- **Ebene 3**: WGI: technical identifier for a product category
- **Ebene 4**: Sub product category (Unterwarengruppe): More specific category of product
- **Ebene 5**: Article family: More specific category of article
- **Ebene 6**: Article name: Specific name of article
- **Special category for fruit and vegetables**: Name of UWG special case for fruits and vegetables

Three more levels for KER, general ledger account, cost category; seems to be mainly used for "products" that are needed for running the company itself.

## Examples

| Level | Example 1 | Example 2 | Example 3 |
|-------|-----------|-----------|-----------|
| **{COL_HAUPTWARENGRUPPE}** | Nahrungsmittel | OBST & GEMÜSE, BLUMEN | |
| **{COL_WG_EBENE_3_WGI}** | 40 TIKO | OBST & GEMÜSE | |
| **{COL_UNTERWARENGRUPPE}** | TIEFKUEHLKOST | OBST | |
| **{COL_ARTIKELFAMILIE}** | EIS | STEINOBST | |
| **{COL_FRUIT_VEG_GROUP}** | N.A. | PFIRSICHE | |
| **{COL_ARTICLE_NAME}** | KEKSSCHNITTE IMPULS | BIO PFIRSICHE 500g PK | REP/ERSATZTEILE MHW MATERIAL |
| **{COL_WG_EBENE_7_KER_POSITION}** | | | IMMOBILIEN [REPARATUR, INSTANDHALTUNG, WARTUNG] |
| **{COL_WG_EBENE_8_SACHKONTO}** | | | REPARATUR, INSTANDHALTUNG - IMMOBILIEN |
| **{COL_WG_EBENE_9_KOSTENKATEGORIE}** | | | REP/ERSATZTEILE MHW MATERIAL |

# Risks Types
* Brutto-Risiko (gross risk):Risk assessment before any mitigation measures. From external supplier. Provided by “Systain” based on general studies. Risks are industry- and country-specific.
* Netto-Risiko (net risk): Adjusted risk assessment for mitigation measures and internal controls.
* Konkretes Risiko (concrete risk): Further adjusted risk assessment based on specific reports (e.g. complain from workers) and some specific audit results (e.g. BSCI). 

# Risk Categories
All risks are categorized by numbers from 1-4 meaning 1 = niedrig, 2 = mittel, 3 = hoch, 4 = sehr hoch.

# Risk Supplier Tiers
* T0: Immediate business partner (e.g. supplier), generally the most important risk to mitigate
* T1: Supplier's supplier (first tier) and production site location
* T1-n: ???
* Tn: Raw material or resource level (e.g. raw material supplier).

# Legal positions ("Rechtspositionen"):
Here are the ten "Rechtspositionen" used for risk assessment:
* Arbeitsschutz
* Diskriminierung
* Entlohnung
* Kinderarbeit
* Koalitionsfreiheit
* Landrechte
* Sicherheitskräfte
* Umweltabkommen
* Umweltbeeinträchtigung
* Zwangsarbeit

# Setup of columns for Risk Types, Risk Supplier Tiers and Legal position
The risk types, risk supplier tiers and legal positions are combined to columns of the type
```python
legal_positions = ["Arbeitsschutz", "Diskriminierung", "Entlohnung", "Kinderarbeit", "Koalitionsfreiheit", "Landrechte", "Sicherheitskräfte", "Umweltabkommen", "Umweltbeeinträchtigung", "Zwangsarbeit"]
supplier_tiers = ["T0 (unmittelbarer Geschäftspartner)", "T1 (Produktionsstätte / Subunternehmen)", "Tn (Rohstoff)"]
netto_risk_columns = [f"Netto-Risiko {{supplier_tier}} - Rechtsposition {{legal_position}}" for supplier_tier in supplier_tiers for legal_position in legal_positions]
brutto_risk_columns = [f"Brutto-Risiko {{supplier_tier}} - Rechtsposition {{legal_position}}" for supplier_tier in supplier_tiers + ["T1-n (tiefere Lieferkette)"] for legal_position in legal_positions]
concrete_risk_columns = [f"Konkretes Risiko {{supplier_tier}} - Rechtsposition {{legal_position}}" for supplier_tier in supplier_tiers for legal_position in legal_positions]
```

Some important words to keep in mind:
Fachbereich = {COL_GROUPING_FACHBEREICH} -> If the users mentions "Fachbereich", they mean this column.
"""

    @classmethod
    def get_description_map(cls) -> dict[DatasetName, str]:
        return {
            DatasetName.BUSINESS_PARTNERS: f"""<purpose> This dataset serves as the master registry of all Geschäftspartner 
    (business partners) within the Schwarz Group's procurement ecosystem, providing comprehensive risk assessments and 
    business intelligence for supplier management and due diligence processes.</purpose>

<data-content> Contains 90,595 unique business partners identified by their "{COL_BUSINESS_PARTNER_ID}" (unique partner ID),
spanning 93 countries with detailed company information including "{COL_BUSINESS_PARTNER_NAME}" (non-unique name of the business partner),
"{COL_COUNTRY}", and a rough industry classification through "{COL_ESTELL_SEKTOR_GROB_RENAMED}" and a more detailed industry classification through
"{COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED}". Each partner has organizational metadata such as "Beschaffende Einheit"
 (unit that does the procurement with that partner), "{COL_GROUPING_FACHBEREICH}" (responsible department for that partner),
and procurement volume indicators through "{COL_REVENUE_TOTAL}" and "Relativer Einkaufswert".
Important note about the "{COL_GROUPING_FACHBEREICH}" column: One of the values is "EK O&G" which translates to "Einkauf Obst & Gemüse". 
The dataset includes 132 risk assessment columns covering Brutto-Risiko, Netto-Risiko, Konkretes Risiko, and their maximum variants across
four supply chain tiers (T0 through Tn) for the ten Rechtspositionen mentioned in the glossary. Partners are categorized by "{COL_SCHWARZ_GROUP_FLAG}"
status and assigned "{COL_NETTO_PRIORISIERUNG}" and "{COL_KONKRETE_PRIORISIERUNG}" for indicating how important that
supplier is based, e.g., on trade volume.</data-content>
""",
            DatasetName.RISK_PER_BUSINESS_PARTNER: f"""<purpose> This granular risk assessment dataset provides the analytical
foundation for detailed supply chain risk management by breaking down each Geschäftspartner's risk profile across multiple
dimensions, enabling precise risk quantification and targeted mitigation strategies.</purpose>

<data-content> Encompasses 1,087,140 risk evaluation records structured as a multi-index. The three indices are 
"{COL_BUSINESS_PARTNER_ID}" (90,595 partners), "Risikotyp" (Brutto, Konkretes Risiko, Netto), and 
"Lieferantenebene" (T0, T1, T1-n, Tn supply chain tiers). Each record, corresponding to a combination of three risk indices, contains
risk scores (0-4 scale) for the ten Rechtspositionen mentioned in the glossary. </data-content>
""",
            DatasetName.RISK_PER_BRANCH: f"""<purpose> This aggregated industry intelligence dataset enables sector-wide risk
analysis and benchmarking by consolidating risk assessments at the intersection of industry classifications, geographic
locations, and supply chain structures for strategic procurement planning.</purpose>

<data-content> Contains 47,388 records structured across four index dimensions: "{COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED}"
(203 detailed industry branches, the naming are technical identifiers), "Risikotyp" (Brutto, Konkretes Risiko, Netto), "Lieferantenebene" (T0, T1, T1-n, Tn),
and "{COL_COUNTRY}" (75 countries). Industry classifications range from agricultural sectors like
"A 04 BEA 003 VEGETABLE AND MELON FARMING" to manufacturing categories such as "D 59 MANUFACTURE OF FURNITURE; MANUFACTURING N.E.C."
Each combination provides risk scores for the ten standard Rechtspositionen from the glossary.</data-content>
""",
            DatasetName.TRANSACTIONS: f"""<purpose> This transactional dataset forms the operational backbone 
for procurement risk documentation, linking individual business activities to detailed risk assessments, product 
categorizations, and supply chain traceability for transaction-level compliance monitoring and risk-weighted procurement analytics.</purpose>

<data-content> Encompasses {Transactions.number_of_rows()} procurement transactions spanning "Datenerfassung Handelsware" ({Transactions.number_of_trading_goods()} trading goods) 
and "Datenerfassung Nicht-Handelsware" ({Transactions.number_of_non_trading_goods()} non-trading goods) over the period 08/2023-07/2024. Each transaction connects
to {Transactions.number_of_unique_business_partners()} unique business partners across {Transactions.number_of_unique_countries()} countries via "{COL_BUSINESS_PARTNER_ID}". Business partners can operate in different branches/sectors
 ("{COL_ESTELL_SEKTOR_GROB_RENAMED}", "{COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED}"). There are revenue indicators "{COL_REVENUE_TOTAL}", "{COL_RELATIVE_PURCHASE_VALUE}".

Transactions include detailed organizational attribution through "{COL_PROCUREMENT_UNIT}", "{COL_SUPPLIED_UNIT}", 
"{COL_GROUPING_FACHBEREICH}". Important note about the "{COL_GROUPING_FACHBEREICH}" column: One of the values is "EK O&G" which translates to "Einkauf Obst & Gemüse". 
The dataset features a 9-level product hierarchy from "{COL_HAUPTWARENGRUPPE}" down to 
"{COL_WG_EBENE_9_KOSTENKATEGORIE}". Whenever data needs to be found for products ("Waren") it makes sense to look at 
ALL levels ("Ebenen"). The lower the level, the more priority a finding should have, as lower level means a more general hit.

The "{COL_PLACE_OF_PRODUCTION_NAME}" values are not unique. Always keep the "{COL_PLACE_OF_PRODUCTION_ID}" when asked about "Produktionsstätten".
When referencing "Rohstoffe", this often refers to "{COL_RISIKOROHSTOFFE}". There is also "{COL_RISKIEST_RESOURCE}" for the riskiest resource.

The dataset includes 132 risk assessment columns covering Brutto-Risiko, Netto-Risiko, Konkretes Risiko, and their maximum variants across
four supply chain tiers (T0 through Tn) for the ten Rechtspositionen mentioned in the glossary. Partners are assigned "{COL_NETTO_PRIORISIERUNG}"
and "{COL_KONKRETE_PRIORISIERUNG}" for indicating how important that supplier is based, e.g., on trade volume.Partners are categorized 
by "{COL_SCHWARZ_GROUP_FLAG}".

Transaction prioritization operates through "Priorisierungs-Scope", "Umsatzschwelle" thresholds, multiple 
"Priorisierungsstufe" classifications, and supplier-level prioritization via "{COL_NETTO_PRIORISIERUNG}" and 
"{COL_KONKRETE_PRIORISIERUNG}", enabling comprehensive risk-based transaction and supplier management. Prioritization 
reflects business partner importance based on trade volume, size, and risk profile.</data-content>
""",
            DatasetName.RESOURCE_RISKS_PROCESSED: f"""<purpose> This raw materials dataset provides 
the foundation for commodity-level risk assessments. It does NOT mean that any resources from any 
of these countries are actually sourced from any supplier. The file is a general overview for risk assessment on resource level.</purpose>

<data-content> Contains 99 records covering 97 unique raw materials ("{COL_ROHSTOFFNAME}") including commodities like "ALUMINIUM (BAUXIT)", 
"HOLZ/BAUMATERIAL", "KOKOSNÜSSE", and specialized materials across agricultural, mineral, and industrial categories. 
Each resource entry includes detailed "{COL_LAENDERHERKUENFTE}" (country origins) for which the risk of that resource has been assessed.
For example, palm oli from "CRI; NIC; GTM; Panama; CAN; ROU; IRL" or wood materials from "NOR; SWE; CHI; DNK; DEU". 
Risk assessments focus exclusively on the "Tn (Rohstoff)" tier with Brutto-Risiko evaluations across all ten Rechtspositionen, 
providing risk scores from 1-4 (notably excluding zero-risk ratings). The geographic coverage spans 34 distinct country combinations.</data-content>
""",
        }

    @classmethod
    def get_description_for_dataset(cls, dataset_name: DatasetName) -> str:
        try:
            return cls.get_description_map()[dataset_name]
        except KeyError:
            raise KeyError(
                f"Dataset '{dataset_name}' not found in description map. "
                f"Available datasets: {list(cls.get_description_map().keys())}"
            )

    @classmethod
    def get_data_files_with_descriptions(
        cls, datasets: list[DatasetName]
    ) -> list[DataFile]:
        data_dir = get_data_dir()
        data_files = []

        for dataset in datasets:
            data_files.append(
                DataFile(
                    file_name=f"{dataset.value}",
                    file_path=Path(data_dir / f"{dataset.value}"),
                    description=cls.get_description_for_dataset(dataset),
                )
            )
        return data_files

    @classmethod
    @lru_cache
    def get_all_data_files_with_descriptions(cls) -> list[DataFile]:
        all_datasets = [dataset for dataset in DatasetName]
        return cls.get_data_files_with_descriptions(all_datasets)
