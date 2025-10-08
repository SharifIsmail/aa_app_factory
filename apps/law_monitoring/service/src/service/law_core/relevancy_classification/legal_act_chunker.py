from loguru import logger

from service.law_core.chunker.chunker import Chunker
from service.law_core.chunker.eur_lex_chunker import EurLexChunker
from service.law_core.chunker.linechunker import LineChunker
from service.law_core.chunker.models import ChunkType, DocumentChunk
from service.law_core.chunker.paragraphchunker import ParagraphChunker
from service.models import RelevancyClassifierLegalActInput


class LegalActChunker:
    def __init__(self, chunker: Chunker):
        self.chunker = chunker

    def _get_eur_lex_chunks(self, url: str) -> list[DocumentChunk]:
        assert isinstance(self.chunker, EurLexChunker), (
            "Chunker must be EurLexChunker for this method"
        )
        chunks = self.chunker.chunk_from_url(url=url)
        logger.info(f"legal act {url} was chunked into {len(chunks)} parts")

        ignore_chunk_types = [ChunkType.TITLE, ChunkType.HEADER, ChunkType.DATE]

        return [chunk for chunk in chunks if chunk.chunk_type not in ignore_chunk_types]

    def get_chunks(
        self, legal_act: RelevancyClassifierLegalActInput
    ) -> list[DocumentChunk]:
        if isinstance(self.chunker, EurLexChunker):
            return self._get_eur_lex_chunks(legal_act.url)
        if isinstance(self.chunker, ParagraphChunker):
            return self.chunker.chunk_document(legal_act.full_text)
        if isinstance(self.chunker, LineChunker):
            return self.chunker.chunk_document(legal_act.full_text)
        raise ValueError(f"unknown chunker: {self.chunker}")
