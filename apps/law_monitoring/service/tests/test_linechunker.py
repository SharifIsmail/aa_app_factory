from typing import List

import pytest

from service.law_core.chunker.linechunker import LineChunker
from service.law_core.chunker.models import ChunkType, DocumentChunk


@pytest.fixture
def sample_law_text() -> str:
    """Sample law text for testing."""
    return """
    Article 1: Scope and Definitions
    This regulation applies to all data processing activities within the European Union.

    Article 2: Data Controller Responsibilities
    Data controllers must implement appropriate technical and organizational measures.

    Article 3: Data Subject Rights
    Data subjects have the right to access, rectify, and erase their personal data.

    Article 4: Penalties and Sanctions
    Violations of this regulation may result in administrative fines up to 4% of annual turnover.
    """


class TestLineChunker:
    line_chunker = LineChunker()

    @pytest.mark.parametrize(
        ("full_text", "expected_chunks"),
        [
            (
                "Article 1: First article.\nArticle 2: Second article.\nArticle 3: Third article.",
                [
                    "Article 1: First article.",
                    "Article 2: Second article.",
                    "Article 3: Third article.",
                ],
            ),
            (
                "Article 1: First article.\n\nArticle 2: Second article.\n\nArticle 3: Third article.",
                [
                    "Article 1: First article.",
                    "",
                    "Article 2: Second article.",
                    "",
                    "Article 3: Third article.",
                ],
            ),
        ],
    )
    def test__split_full_text_into_chunks_by_lines_splits_text_correctly(
        self,
        full_text: str,
        expected_chunks: List[str],
    ) -> None:
        chunks = self.line_chunker._split_full_text_into_chunks_by_lines(full_text)
        assert chunks == expected_chunks

    @pytest.mark.parametrize(
        ("full_text", "expected_chunks"),
        [
            (
                "Article 1: First article.\nArticle 2: Second article.\nArticle 3: Third article.",
                [
                    DocumentChunk(
                        chunk_type=ChunkType.LINE, content="Article 1: First article."
                    ),
                    DocumentChunk(
                        chunk_type=ChunkType.LINE, content="Article 2: Second article."
                    ),
                    DocumentChunk(
                        chunk_type=ChunkType.LINE, content="Article 3: Third article."
                    ),
                ],
            ),
            (
                "Article 1: First article.\n\nArticle 2: Second article.\n\nArticle 3: Third article.",
                [
                    DocumentChunk(
                        chunk_type=ChunkType.LINE, content="Article 1: First article."
                    ),
                    DocumentChunk(chunk_type=ChunkType.LINE, content=""),
                    DocumentChunk(
                        chunk_type=ChunkType.LINE, content="Article 2: Second article."
                    ),
                    DocumentChunk(chunk_type=ChunkType.LINE, content=""),
                    DocumentChunk(
                        chunk_type=ChunkType.LINE, content="Article 3: Third article."
                    ),
                ],
            ),
        ],
    )
    def test_chunk_document(
        self,
        full_text: str,
        expected_chunks: List[str],
    ) -> None:
        chunks = self.line_chunker.chunk_document(full_text)
        assert chunks == expected_chunks

        all_chunks_joined = self.line_chunker.join_chunks(
            chunks=[chunk.content for chunk in chunks],
            number_of_chunks_to_join=len(chunks),
        )
        assert all_chunks_joined == [full_text]
