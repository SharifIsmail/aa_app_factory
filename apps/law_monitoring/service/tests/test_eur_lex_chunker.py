import pytest

from service.law_core.chunker.eur_lex_chunker import EurLexChunker


class TestEurLexChunker:
    """
    Test class for EurLexChunker to ensure it can fetch and chunk documents correctly.
    """

    chunker = EurLexChunker()

    @pytest.mark.parametrize(
        "url",
        [
            "http://publications.europa.eu/resource/cellar/d34251c8-d865-11ef-be2a-01aa75ed71a1.0006.03/DOC_1",
            "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202501711",
            "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202501525&qid=1754640466370",
            "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202501096",
            "https://publications.europa.eu/resource/cellar/10b95020-3b5e-11f0-8a44-01aa75ed71a1.0006.03/DOC_1",
            "https://publications.europa.eu/resource/cellar/0dcc962e-d866-11ef-be2a-01aa75ed71a1.0006.03/DOC_1",
            "https://publications.europa.eu/resource/cellar/256cb68f-d866-11ef-be2a-01aa75ed71a1.0006.03/DOC_1",
            "https://publications.europa.eu/resource/cellar/1779b2d5-d866-11ef-be2a-01aa75ed71a1",
        ],
    )
    def test_chunk_from_url(self, url: str) -> None:
        chunks = self.chunker.chunk_from_url(url=url)
        assert len(chunks) > 1
        summary = self.chunker.get_chunk_summary(chunks)
        for chunk_type, count in summary.items():
            print(f"  {chunk_type}: {count}")

        print("\nDetailed Chunk Information:")
        for i, chunk in enumerate(chunks):
            print(f"\n{i + 1}. {chunk.chunk_type.value.upper()}")
            if chunk.title:
                print(f"   Title: {chunk.title}")
            if chunk.section_number:
                print(f"   Section: {chunk.section_number}")
            if chunk.subsection_number:
                print(f"   Subsection: {chunk.subsection_number}")
            if chunk.paragraph_number:
                print(f"   Paragraph: {chunk.paragraph_number}")
            print(f"   Level: {chunk.level}")
            print(f"   Content length: {len(chunk.content)} chars")
            print(f"   Content preview: {chunk.content[:100].replace(chr(10), ' ')}...")

        # Export to JSON
        json_output = self.chunker.export_chunks_to_json(chunks)
        print(f"\nJSON output length: {len(json_output)} characters")

    def test_whereas_chunking(self) -> None:
        """
        Test that WHEREAS clauses are properly split into individual chunks per numbered article.
        """
        # Sample WHEREAS content with numbered articles
        sample_whereas_text = """Whereas:
(1)
On 6 December 2024, the European Commission initiated an anti-dumping investigation with regard to imports of high-pressure seamless steel cylinders originating in the People's Republic of China.

(2)
The Commission initiated the investigation following a complaint lodged on 24 October 2024 by five companies, Cylinders Holding a.s., Dalmine S.p.A. (Tenaris), Eurocylinder Systems AG, Faber Industrie S.p.A., and Worthington Cylinders GmbH.

(3)
The Commission made imports of the product concerned subject to registration by Commission Implementing Regulation (EU) 2025/531.

(4)
In the Notice of Initiation, the Commission invited interested parties to contact it in order to participate in the investigation."""

        # Process the whereas content
        whereas_chunks = self.chunker._process_whereas_content(sample_whereas_text, 0)

        # Verify that we get multiple chunks (one per numbered article)
        assert len(whereas_chunks) >= 4, (
            f"Expected at least 4 whereas chunks, got {len(whereas_chunks)}"
        )

        # Verify that each chunk has the correct properties
        for i, chunk in enumerate(whereas_chunks, 1):
            assert chunk.chunk_type.value == "whereas", (
                f"Chunk {i} should be WHEREAS type"
            )
            assert chunk.paragraph_number == str(i), (
                f"Chunk {i} should have paragraph_number '{i}'"
            )
            assert chunk.level == 2, f"Chunk {i} should have level 2"
            assert f"({i})" in chunk.content, f"Chunk {i} should contain '({i})'"
            assert chunk.title == f"Whereas article ({i})", (
                f"Chunk {i} should have correct title"
            )

        print(f"\nWhereas chunking test passed: {len(whereas_chunks)} chunks created")
        for i, chunk in enumerate(whereas_chunks):
            print(
                f"  Chunk {i + 1}: paragraph ({chunk.paragraph_number}), length: {len(chunk.content)} chars"
            )

    def test_whereas_chunking_no_articles(self) -> None:
        """
        Test WHEREAS content that doesn't have numbered articles falls back to single chunk.
        """
        # Sample WHEREAS content without numbered articles
        sample_whereas_text = """Whereas:
This is a simple whereas clause without numbered articles.
It should be treated as a single chunk."""

        # Process the whereas content
        whereas_chunks = self.chunker._process_whereas_content(sample_whereas_text, 0)

        # Verify that we get a single chunk
        assert len(whereas_chunks) == 1, (
            f"Expected 1 whereas chunk, got {len(whereas_chunks)}"
        )

        chunk = whereas_chunks[0]
        assert chunk.chunk_type.value == "whereas", "Chunk should be WHEREAS type"
        assert chunk.paragraph_number is None, "Chunk should not have paragraph_number"
        assert chunk.level == 1, "Chunk should have level 1"
        assert chunk.title == "Whereas clause", "Chunk should have correct title"

        print(
            "Whereas chunking fallback test passed: single chunk created for non-numbered content"
        )
