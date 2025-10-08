import pytest

from service.law_core.chunker.models import ChunkType, DocumentChunk
from service.law_core.relevancy_classification.citation_tool import LLMCitationTool
from service.law_core.tools.llm_completion_tool import LLMCompletionTool
from service.models import TeamRelevancy


class LLM(LLMCompletionTool):
    def __init__(self, response: str) -> None:
        self.response = response

    def forward(self, prompt: str, purpose: str) -> str:
        return self.response


@pytest.mark.parametrize(
    "raw_response, expected",
    [
        ("#DECISION: ok\n#RESULT: YES", True),
        ("#DECISION: ok\n#RESULT: NO", False),
    ],
)
def test_single_chunk(raw_response: str, expected: bool) -> None:
    tool = LLMCitationTool(llm_completion_tool=LLM(raw_response), max_retries=0)
    team = TeamRelevancy(team_name="T", is_relevant=True, reasoning="Claim")
    chunks = [
        DocumentChunk(chunk_type=ChunkType.PARAGRAPH, content="A", order_index=0),
    ]

    citations = tool.cite(team_relevancy=team, chunks=chunks)

    assert len(citations) == 1
    assert citations[0].factfulness.is_factual == expected
    assert citations[0].chunk.order_index == 0


def test_citations_are_sorted() -> None:
    tool = LLMCitationTool(
        llm_completion_tool=LLM("#DECISION: ok\n#RESULT: YES"),
        max_retries=0,
    )
    team = TeamRelevancy(team_name="T", is_relevant=True, reasoning="Claim")
    chunks = [
        DocumentChunk(chunk_type=ChunkType.PARAGRAPH, content="C", order_index=2),
        DocumentChunk(chunk_type=ChunkType.PARAGRAPH, content="A", order_index=0),
        DocumentChunk(chunk_type=ChunkType.PARAGRAPH, content="B", order_index=1),
    ]

    citations = tool.cite(team_relevancy=team, chunks=chunks)

    assert [c.chunk.order_index for c in citations] == [0, 1, 2]
    assert all(c.factfulness.is_factual for c in citations)


def test_non_relevant_team_returns_empty_citations() -> None:
    """Test that non-relevant teams return empty citation lists for memory optimization."""
    # LLM response doesn't matter since we short-circuit for non-relevant teams
    tool = LLMCitationTool(
        llm_completion_tool=LLM("#DECISION: ok\n#RESULT: YES"),
        max_retries=0,
    )
    team = TeamRelevancy(
        team_name="Legal",
        is_relevant=False,
        reasoning="Not applicable to legal matters",
    )
    chunks = [
        DocumentChunk(chunk_type=ChunkType.PARAGRAPH, content="A", order_index=0),
        DocumentChunk(chunk_type=ChunkType.PARAGRAPH, content="B", order_index=1),
        DocumentChunk(chunk_type=ChunkType.PARAGRAPH, content="C", order_index=2),
    ]

    citations = tool.cite(team_relevancy=team, chunks=chunks)

    # Should return empty list for non-relevant teams (memory optimization)
    assert citations == []
    assert len(citations) == 0
