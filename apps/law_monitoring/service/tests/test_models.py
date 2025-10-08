from typing import List

import pytest

from service.models import Citation, TeamRelevancyWithCitations


class TestTeamRelevancyWithCitations:
    @pytest.mark.parametrize("is_relevant", [True, False])
    @pytest.mark.parametrize("citations", [[], None])
    def test_not_relevant_with_empty_list_of_citations(
        self, is_relevant: bool, citations: List[Citation] | None
    ) -> None:
        team_relevancy = TeamRelevancyWithCitations(
            team_name="Test Team",
            is_relevant=is_relevant,
            reasoning="Test Reasoning",
            citations=citations,
        )
        assert team_relevancy.is_relevant == is_relevant
        assert team_relevancy.citations == citations
