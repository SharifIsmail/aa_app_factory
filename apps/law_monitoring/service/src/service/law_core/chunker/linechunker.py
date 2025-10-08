from typing import List

from service.law_core.chunker.chunker import Chunker
from service.law_core.chunker.models import ChunkType, DocumentChunk


class LineChunker(Chunker):
    def _split_full_text_into_chunks_by_lines(self, text: str) -> list[str]:
        return text.split("\n")

    def chunk_document(self, text: str) -> List[DocumentChunk]:
        """
        Splits the document into chunks based on line breaks.
        Each line is treated as a separate chunk.

        Args:
            text (str): The text to be chunked.

        Returns:
            list[str]: A list of text chunks, each representing a line.
        """
        lines = self._split_full_text_into_chunks_by_lines(text)
        document_chunks = []

        for index, line in enumerate(lines):
            document_chunks.append(
                DocumentChunk(
                    content=line, chunk_type=ChunkType.LINE, order_index=index
                )
            )
        return document_chunks

    def _join_chunks_on(self) -> str:
        return "\n"
