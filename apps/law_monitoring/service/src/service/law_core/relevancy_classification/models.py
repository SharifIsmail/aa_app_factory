from enum import StrEnum


class ChunkStrategy(StrEnum):
    """Enumeration for chunking strategies."""

    PARAGRAPH = "paragraph"
    EUR_LEX = "eur_lex"
    LINES = "lines"


class LegalActContext(StrEnum):
    """Enumeration for chunking strategies."""

    FULL_TEXT = "full_text"
    SUMMARY = "summary"
