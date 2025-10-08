from typing import List

from loguru import logger

from service.law_core.chunker.models import DocumentChunk, DocumentChunksGroup


class Chunker:
    def chunk_document(self, text: str) -> List[DocumentChunk]:
        raise NotImplementedError()

    def _join_chunks_on(self) -> str:
        raise NotImplementedError()

    def join_chunks(
        self, chunks: list[str], number_of_chunks_to_join: int
    ) -> list[str]:
        """Join chunks into larger parts based on the join_chunks parameter.

        Args:
            chunks: List of text chunks

        Returns:
            List of joined text chunks
        """
        if number_of_chunks_to_join < 1:
            raise ValueError("join_chunks must be at least 1")

        joined_chunks = []
        for i in range(0, len(chunks), number_of_chunks_to_join):
            joined_chunk = self._join_chunks_on().join(
                chunks[i : i + number_of_chunks_to_join]
            )
            joined_chunks.append(joined_chunk)
        logger.debug(f"joined {len(chunks)} chunks into {len(joined_chunks)} groups")

        return joined_chunks

    def join_document_chunks(
        self, chunks: list[DocumentChunk], number_of_chunks_to_join: int
    ) -> list[DocumentChunksGroup]:
        if number_of_chunks_to_join < 1:
            raise ValueError("join_chunks must be at least 1")

        joined_chunks_groups: List[DocumentChunksGroup] = []
        for i in range(0, len(chunks), number_of_chunks_to_join):
            chunks_to_join = chunks[i : i + number_of_chunks_to_join]
            assert len(set(chunk.chunk_type for chunk in chunks_to_join)) == 1, (
                "can only join chunks of the same type"
            )
            first_chunk = chunks_to_join[0]
            last_chunk = chunks_to_join[-1]

            joined_content_list = self.join_chunks(
                [chunk.content for chunk in chunks_to_join],
                number_of_chunks_to_join=number_of_chunks_to_join,
            )
            assert len(joined_content_list) == 1
            concatenation_of_chunk_contents = joined_content_list[0]

            document_chunks_group = DocumentChunksGroup(
                chunks=chunks_to_join,
                concatenation_of_chunk_contents=concatenation_of_chunk_contents,
                start_pos_first_chunk=first_chunk.start_pos,
                end_pos_last_chunk=last_chunk.end_pos,
            )
            joined_chunks_groups.append(document_chunks_group)

        logger.debug(
            f"joined {len(chunks)} DocumentChunks into {len(joined_chunks_groups)} groups"
        )

        return joined_chunks_groups
