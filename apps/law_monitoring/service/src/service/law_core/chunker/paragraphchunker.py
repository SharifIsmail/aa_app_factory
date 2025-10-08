from typing import List

from service.law_core.chunker.chunker import Chunker
from service.law_core.chunker.models import ChunkType, DocumentChunk


class ParagraphChunker(Chunker):
    def _split_law_text_into_chunks_by_paragraph(self, text: str) -> list[str]:
        # Split by paragraphs, assuming double newlines indicate a new paragraph
        return text.split("\n\n")

    def chunk_document(self, text: str) -> List[DocumentChunk]:
        """
        Splits the document into chunks based on paragraphs.
        Each paragraph is treated as a separate chunk.

        Args:
            text (str): The text to be chunked.

        Returns:
            list[str]: A list of text chunks, each representing a paragraph.
        """
        paragraphs = self._split_law_text_into_chunks_by_paragraph(text)
        document_chunks = []
        for index, paragraph in enumerate(paragraphs):
            document_chunks.append(
                DocumentChunk(
                    content=paragraph,
                    chunk_type=ChunkType.PARAGRAPH,
                    order_index=index,
                )
            )

        return document_chunks

    def _join_chunks_on(self) -> str:
        return "\n\n"
