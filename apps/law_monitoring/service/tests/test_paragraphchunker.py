from typing import List

import pytest

from service.law_core.chunker.models import ChunkType, DocumentChunk
from service.law_core.chunker.paragraphchunker import ParagraphChunker


class TestParagraphChunker:
    paragraph_chunker = ParagraphChunker()

    @pytest.mark.parametrize(
        ("full_text", "expected_chunks"),
        [
            (
                "Article 1: First article.\n\nArticle 2: Second article.\n\nArticle 3: Third article.",
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
                    "Article 2: Second article.",
                    "Article 3: Third article.",
                ],
            ),
        ],
    )
    def test__split_law_text_into_chunks_by_paragraph_splits_text_correctly(
        self,
        full_text: str,
        expected_chunks: List[str],
    ) -> None:
        chunks = self.paragraph_chunker._split_law_text_into_chunks_by_paragraph(
            full_text
        )
        assert chunks == expected_chunks

    @pytest.mark.parametrize(
        ("full_text", "expected_chunks"),
        [
            (
                "Article 1: First article.\n\nArticle 2: Second article.\n\nArticle 3: Third article.",
                [
                    DocumentChunk(
                        chunk_type=ChunkType.PARAGRAPH,
                        content="Article 1: First article.",
                    ),
                    DocumentChunk(
                        chunk_type=ChunkType.PARAGRAPH,
                        content="Article 2: Second article.",
                    ),
                    DocumentChunk(
                        chunk_type=ChunkType.PARAGRAPH,
                        content="Article 3: Third article.",
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
        chunks = self.paragraph_chunker.chunk_document(full_text)
        assert chunks == expected_chunks

        all_chunks_joined = self.paragraph_chunker.join_chunks(
            chunks=[chunk.content for chunk in chunks],
            number_of_chunks_to_join=len(chunks),
        )
        assert all_chunks_joined == [full_text]
