import pytest

from service.law_core.chunker.chunker import Chunker
from service.law_core.chunker.linechunker import LineChunker
from service.law_core.chunker.models import (
    ChunkType,
    DocumentChunk,
    DocumentChunksGroup,
)
from service.law_core.chunker.paragraphchunker import ParagraphChunker


class TestChunker:
    def test_join_chunks(self) -> None:
        with pytest.raises(ValueError):
            chunker = Chunker()
            chunker.join_chunks(["foo", "bar"], number_of_chunks_to_join=0)

    @pytest.mark.parametrize(
        ("join_chunks", "chunker", "expected_joined_chunks"),
        [
            (
                1,
                ParagraphChunker(),
                [
                    "chunk 1",
                    "chunk 2",
                    "chunk 3",
                ],
            ),
            (
                1,
                LineChunker(),
                [
                    "chunk 1",
                    "chunk 2",
                    "chunk 3",
                ],
            ),
            (
                2,
                ParagraphChunker(),
                [
                    "chunk 1\n\nchunk 2",
                    "chunk 3",
                ],
            ),
            (
                2,
                LineChunker(),
                [
                    "chunk 1\nchunk 2",
                    "chunk 3",
                ],
            ),
            (
                3,
                ParagraphChunker(),
                [
                    "chunk 1\n\nchunk 2\n\nchunk 3",
                ],
            ),
            (
                3,
                LineChunker(),
                [
                    "chunk 1\nchunk 2\nchunk 3",
                ],
            ),
            (
                4,
                ParagraphChunker(),
                [
                    "chunk 1\n\nchunk 2\n\nchunk 3",
                ],
            ),
            (
                4,
                LineChunker(),
                [
                    "chunk 1\nchunk 2\nchunk 3",
                ],
            ),
        ],
    )
    def test__join_chunks(
        self,
        join_chunks: int,
        expected_joined_chunks: list[str],
        chunker: Chunker,
    ) -> None:
        """Test that chunks are joined correctly."""
        chunks = [
            "chunk 1",
            "chunk 2",
            "chunk 3",
        ]

        result = chunker.join_chunks(chunks, number_of_chunks_to_join=join_chunks)

        assert result == expected_joined_chunks

    @pytest.mark.parametrize("chunker", [ParagraphChunker(), LineChunker()])
    @pytest.mark.parametrize(
        "document_chunks, number_of_chunks_to_join, expected_document_chunks_groups",
        [
            (
                [
                    DocumentChunk(
                        chunk_type=ChunkType.LINE,
                        content="line 1",
                        start_pos=0,
                        end_pos=5,
                    ),
                    DocumentChunk(
                        chunk_type=ChunkType.LINE,
                        content="line 2",
                        start_pos=7,
                        end_pos=12,
                    ),
                ],
                2,
                [
                    DocumentChunksGroup(
                        chunks=[
                            DocumentChunk(
                                chunk_type=ChunkType.LINE,
                                content="line 1",
                                start_pos=0,
                                end_pos=5,
                            ),
                            DocumentChunk(
                                chunk_type=ChunkType.LINE,
                                content="line 2",
                                start_pos=7,
                                end_pos=12,
                            ),
                        ],
                        concatenation_of_chunk_contents="line 1\nline 2",
                        start_pos_first_chunk=0,
                        end_pos_last_chunk=12,
                    )
                ],
            ),
            (
                [
                    DocumentChunk(
                        chunk_type=ChunkType.LINE,
                        content="line 1",
                        start_pos=0,
                        end_pos=5,
                    ),
                    DocumentChunk(
                        chunk_type=ChunkType.LINE,
                        content="line 2",
                        start_pos=7,
                        end_pos=12,
                    ),
                ],
                1,
                [
                    DocumentChunksGroup(
                        chunks=[
                            DocumentChunk(
                                chunk_type=ChunkType.LINE,
                                content="line 1",
                                start_pos=0,
                                end_pos=5,
                            )
                        ],
                        concatenation_of_chunk_contents="line 1",
                        start_pos_first_chunk=0,
                        end_pos_last_chunk=5,
                    ),
                    DocumentChunksGroup(
                        chunks=[
                            DocumentChunk(
                                chunk_type=ChunkType.LINE,
                                content="line 2",
                                start_pos=7,
                                end_pos=12,
                            )
                        ],
                        concatenation_of_chunk_contents="line 2",
                        start_pos_first_chunk=7,
                        end_pos_last_chunk=12,
                    ),
                ],
            ),
            (
                [
                    DocumentChunk(
                        chunk_type=ChunkType.LINE,
                        content="line 1",
                        start_pos=0,
                        end_pos=5,
                    ),
                    DocumentChunk(
                        chunk_type=ChunkType.LINE,
                        content="line 2",
                        start_pos=7,
                        end_pos=12,
                    ),
                    DocumentChunk(
                        chunk_type=ChunkType.LINE,
                        content="line 3",
                        start_pos=14,
                        end_pos=19,
                    ),
                ],
                2,
                [
                    DocumentChunksGroup(
                        chunks=[
                            DocumentChunk(
                                chunk_type=ChunkType.LINE,
                                content="line 1",
                                start_pos=0,
                                end_pos=5,
                            ),
                            DocumentChunk(
                                chunk_type=ChunkType.LINE,
                                content="line 2",
                                start_pos=7,
                                end_pos=12,
                            ),
                        ],
                        concatenation_of_chunk_contents="line 1\nline 2",
                        start_pos_first_chunk=0,
                        end_pos_last_chunk=12,
                    ),
                    DocumentChunksGroup(
                        chunks=[
                            DocumentChunk(
                                chunk_type=ChunkType.LINE,
                                content="line 3",
                                start_pos=14,
                                end_pos=19,
                            )
                        ],
                        concatenation_of_chunk_contents="line 3",
                        start_pos_first_chunk=14,
                        end_pos_last_chunk=19,
                    ),
                ],
            ),
        ],
    )
    def test_join_document_chunks(
        self,
        chunker: Chunker,
        document_chunks: list[DocumentChunk],
        number_of_chunks_to_join: int,
        expected_document_chunks_groups: list[DocumentChunksGroup],
    ) -> None:
        chunker = LineChunker()
        result = chunker.join_document_chunks(
            chunks=document_chunks, number_of_chunks_to_join=number_of_chunks_to_join
        )
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, DocumentChunksGroup)
        assert result == expected_document_chunks_groups
