from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, List, Optional

from pydantic import BaseModel, field_serializer


class ChunkType(StrEnum):
    """Types of document chunks identified in EUR-Lex documents."""

    HEADER = "header"
    TITLE = "title"
    DATE = "date"
    SUBJECT = "subject"
    PREAMBLE = "preamble"
    COMMISSION_DECLARATION = "commission_declaration"
    LEGAL_BASIS = "legal_basis"
    WHEREAS = "whereas"
    MAIN_SECTION = "main_section"
    SUBSECTION = "subsection"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    ANNEX = "annex"
    FOOTER = "footer"
    REFERENCE = "reference"
    LINE = "line"


@dataclass(frozen=True)
class DocumentChunk:
    """Represents a semantic chunk of a legal document."""

    chunk_type: ChunkType
    content: str
    order_index: int  # the order of the chunk relative to the original non-chunked text. This is used to identify the order of the chunks in the original text.
    section_number: Optional[str] = None
    subsection_number: Optional[str] = None
    paragraph_number: Optional[str] = None
    title: Optional[str] = None
    level: int = 0
    start_pos: int | None = None
    end_pos: int | None = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert chunk to dictionary format."""
        return {
            "chunk_type": self.chunk_type.value,
            "content": self.content,
            "section_number": self.section_number,
            "subsection_number": self.subsection_number,
            "paragraph_number": self.paragraph_number,
            "title": self.title,
            "level": self.level,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "metadata": self.metadata or {},
        }


class DocumentChunksGroup(BaseModel):
    chunks: List[DocumentChunk]
    concatenation_of_chunk_contents: str
    start_pos_first_chunk: int | None = None
    end_pos_last_chunk: int | None = None

    class Config:
        frozen = True

    @field_serializer("chunks")
    def serialize_chunks(self, chunks: List[DocumentChunk]) -> List[Dict]:
        return [chunk.to_dict() for chunk in chunks]
