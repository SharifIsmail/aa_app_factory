"""
Centralized definitions of dataset column names used across tools.

These constants map to the exact German column headers present in the source data.
"""

# Business partner identification
COL_BUSINESS_PARTNER_ID: str = "Eindeutige GP-Kennzahl"
COL_BUSINESS_PARTNER_NAME: str = "Name Geschäftspartner (GP)"
COL_BUSINESS_PARTNER_UST_ID: str = "Ust.-ID"

# Business partner properties
COL_PART_OF_SCHWARZ = (
    "Minderheitsbeteiligung / Tochter / Gruppenunternehmen innerhalb der Schwarzgruppe"
)

# Data source and country
COL_DATA_SOURCE: str = "Datenquelle / Datenherkunft"
COL_COUNTRY: str = "Land / Sitz des Geschäftspartners (GP)"

# Business partner metadata columns
COL_PLACE_OF_PRODUCTION_ID: str = "Produktionsstätten ID"
COL_PLACE_OF_PRODUCTION_NAME: str = "Produktionsstätten Name"
COL_PLACE_OF_PRODUCTION_COUNTRY = "Land / Sitz der Produktionsstätte / Subunternehmer"
COL_PROCUREMENT_UNIT: str = "Beschaffende Einheit"
COL_SUPPLIED_UNIT: str = "Belieferte Einheit"
COL_RELATIVE_PURCHASE_VALUE = (
    "Relativer Einkaufswert (EK-Wert) gesamt des Geschäftspartner (GP)"
)
COL_RESPONSIBLE_DEPARTMENT = "Verantwortliche Fachabteilung"
COL_REVENUE_THRESHOLD = "Umsatzschwelle"

# Product hierarchy (WG Ebenen)
COL_HAUPTWARENGRUPPE: str = "WG Ebene 1 - Hauptwarengruppe (HWG)"
COL_WG_EBENE_3_WGI: str = "WG Ebene 3 - WGI"
COL_UNTERWARENGRUPPE: str = "WG Ebene 4 - Unterwarengruppe (UWG)"
COL_ARTIKELFAMILIE: str = "WG Ebene 5 - Artikelfamilie"
COL_ARTICLE_NAME: str = "WG Ebene 6 - Artikelbezeichnung"
COL_WG_EBENE_7_KER_POSITION: str = "WG Ebene 7 - KER-Position"
COL_WG_EBENE_8_SACHKONTO: str = "WG Ebene 8 - Sachkonto"
COL_WG_EBENE_9_KOSTENKATEGORIE: str = "WG Ebene 9 (Kostenkategorie)"
COL_FINEST_PRODUCT_LEVEL = "Feinste Produktebene / Dienstleistungsebene"

# Special fruit/vegetable grouping
COL_FRUIT_VEG_GROUP: str = 'Artikelgruppe für UWG "Obst" und "Gemüse"'

# ID columns for the hierarchy levels
COL_ID_HAUPTWARENGRUPPE: str = "Nummer WG Ebene 1 - Hauptwarengruppe (HWG)"
COL_ID_WG_EBENE_3_WGI: str = "Nummer WG Ebene 3 - WGI"
COL_ID_UNTERWARENGRUPPE: str = "Nummer WG Ebene 4 - Unterwarengruppe (UWG)"
COL_ID_ARTIKELFAMILIE: str = "Nummer WG Ebene 5 - Artikelfamilie"
COL_ID_ARTICLE_NAME: str = "Nummer WG Ebene 6 - Artikelbezeichnung"
COL_ID_ARTICLE_NAME_CONCRETE_FILE: str = (
    "Nummer WG Ebene 6 - Artikelbezeichnung / Artikel IAN"
)
COL_ID_FRUIT_VEG_GROUP: str = 'Nummer Artikelgruppe für UWG "Obst" und "Gemüse"2'
COL_ID_WG_EBENE_7_KER_POSITION: str = "Nummer WG Ebene 7 - KER-Position"
COL_ID_WG_EBENE_8_SACHKONTO: str = "Nummer WG Ebene 8 - Sachkonto"
COL_ID_WG_EBENE_9_KOSTENKATEGORIE: str = "Nummer WG Ebene 9 (Kostenkategorie)"
COL_ID_ARTICLE_UNIQUE: str = "artikel_unique_id"

# Partner sector classification
COL_ESTELL_SEKTOR_GROB_RAW: str = (
    "estell Sektor grob (Branche grob) des Geschäftspartners (GP)"
)
COL_ESTELL_SEKTOR_GROB_RENAMED: str = "estell Sektor grob (Branche grob)"

COL_ESTELL_SEKTOR_DETAILLIERT_RAW: str = (
    "estell Sektor detailliert (Branche detailliert) des Geschäftspartners (GP)"
)
COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED: str = (
    "estell Sektor detailliert (Branche detailliert)"
)

# Risk-related columns
COL_RISIKOROHSTOFFE: str = "Risikorohstoffe"
COL_RISKIEST_RESOURCE: str = "Risikoreichster Rohstoff"
COL_RISKIEST_RESOURCE_KONKRET: str = "konkreter Risikoreichster Rohstoff"
COL_RISKIEST_RESOURCE_BRUTTO: str = "Brutto Risikoreichster Rohstoff"
COL_RISKIEST_RESOURCE_NETTO: str = "Netto Risikoreichster Rohstoff"

# Result assembly helper columns (used by some tools as output)
COL_GEFUNDENE_RISIKOROHSTOFFE: str = "Gefundene Risikorohstoffe"
COL_ROHSTOFFNAME: str = "Rohstoffname"
COL_LAENDERHERKUENFTE: str = "Länderherkünfte"
OUTPUT_COL_ARTICLE_CATEGORY: str = "Artikelgruppe"
OUTPUT_COL_ARTICLE_CATEGORY_SOURCE: str = "Ursprung der Artikelgruppe"

# Business partner prioritization and org metadata
COL_GROUPING_FACHBEREICH: str = "Verantwortlicher Fachbereich / Einkaufsbereich"
COL_PRIORISIERUNGS_SCOPE: str = "Priorisierungs-Scope für Branchen (Estell-Sektoren)"
COL_NETTO_PRIORISIERUNG: str = "Netto Priorisierung / Priorisierungsstufe (Priostufe)"
COL_KONKRETE_PRIORISIERUNG: str = (
    "Konkrete Priorisierung / Priorisierungsstufe (Priostufe)"
)
COL_BRUTTO_PRIORISIERUNG: str = "Brutto Priorisierung / Priorisierungsstufe (Priostufe)"
COL_REVENUE_TOTAL: str = "Einkaufswert je GP (Gesamt)"
COL_SCHWARZBESCHAFFUNG: str = "Verhandelt duch SBES (Schwarz Beschaffung)"
COL_SCHWARZ_GROUP_FLAG: str = (
    "Minderheitsbeteiligung / Tochter / Gruppenunternehmen innerhalb der Schwarzgruppe"
)

# Time period columns
COL_BETRACHTUNGSZEITRAUM_START: str = "Betrachtungszeitraum Start"
COL_BETRACHTUNGSZEITRAUM_ENDE: str = "Betrachtungszeitraum Ende"
COL_BETRACHTUNGSZEITRAUM_RANGE: str = "Betrachtungszeitraum der erfassten Daten"

# Others
COL_MARKENTYP_HANDELSWARE = (
    "Markentyp Handelsware (M=Marke / Eigenmarke=EM / HM=Handelsmarke)"
)
COL_ABWICKLUNGSART = "Abwicklungsart"

# Legal positions columns
LEGAL_CATEGORIES = [
    "Arbeitsschutz",
    "Diskriminierung",
    "Entlohnung",
    "Kinderarbeit",
    "Koalitionsfreiheit",
    "Landrechte",
    "Sicherheitskräfte",
    "Umweltabkommen",
    "Umweltbeeinträchtigung",
    "Zwangsarbeit",
]

COL_CONCRETE_RISK_T0_LEGAL_POSITIONS = [
    f"Konkretes Risiko T0 (unmittelbarer Geschäftspartner) - Rechtsposition {category}"
    for category in LEGAL_CATEGORIES
]

COL_GROSS_RISK_T0_LEGAL_POSITIONS = [
    f"Brutto-Risiko T0 (unmittelbarer Geschäftspartner) - Rechtsposition {category}"
    for category in LEGAL_CATEGORIES
]

COL_GROSS_RISK_T1_LEGAL_POSITIONS = [
    f"Brutto-Risiko T1 (Produktionsstätte / Subunternehmen) - Rechtsposition {category}"
    for category in LEGAL_CATEGORIES
]
COL_GROSS_RISK_TN_LEGAL_POSITIONS = [
    f"Brutto-Risiko Tn (Rohstoff) - Rechtsposition {category}"
    for category in LEGAL_CATEGORIES
]
COL_GROSS_RISK_T1_N_LEGAL_POSITIONS = [
    f"Brutto-Risiko T1-n (tiefere Lieferkette) - Rechtsposition {category}"
    for category in LEGAL_CATEGORIES
]

# Common empty/null indicators
EMPTY_VALUES: list[str | None] = ["N.A.", "nan", "", None, "N.A.N.A.N.A."]


COL_PRIMARY_KEY: str = "Pseudo-Primärschlüssel"

PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS_BASE: tuple[str, ...] = (
    COL_BUSINESS_PARTNER_ID,
    COL_PROCUREMENT_UNIT,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
)
HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS: tuple[str, ...] = (
    *PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS_BASE,
    COL_REVENUE_TOTAL,
    COL_MARKENTYP_HANDELSWARE,
    COL_ARTIKELFAMILIE,
    COL_ARTICLE_NAME,
    COL_ID_ARTICLE_NAME,
)
NICHT_HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS: tuple[str, ...] = (
    *PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS_BASE,
    COL_WG_EBENE_7_KER_POSITION,
    COL_ID_WG_EBENE_8_SACHKONTO,
    COL_ID_WG_EBENE_9_KOSTENKATEGORIE,
)
