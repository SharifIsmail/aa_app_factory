"""remove_claim_field_from_citations_data_migration

This data migration removes the redundant 'claim' field from existing Citation objects
in the database. The claim field was redundant because it always contained the same
value as the team's reasoning field, leading to massive memory waste.

This migration:
1. Finds all laws with team_relevancy_classification data containing citations
2. Removes the 'claim' field from each citation object
3. Preserves all other citation data (chunk, factfulness)

Benefits:
- Massive memory savings (10-100x reduction in citation storage)
- Eliminates redundant data storage
- No functional impact (claim was never used independently of team reasoning)

Revision ID: 44a161304b00
Revises: 4b3134666891
Create Date: 2025-09-18 17:14:51.996152

"""

from typing import Any, Dict, List, Sequence, Union

import sqlalchemy as sa
from loguru import logger

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "44a161304b00"
down_revision: Union[str, Sequence[str], None] = "4b3134666891"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def clean_citation_claims(
    citations: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], int]:
    """Remove 'claim' field from citation objects.

    Args:
        citations: List of citation dictionaries

    Returns:
        Tuple of (cleaned_citations, claims_removed_count)
    """
    if not isinstance(citations, list):
        return citations, 0

    cleaned_citations = []
    claims_removed = 0

    for citation in citations:
        if not isinstance(citation, dict):
            cleaned_citations.append(citation)
            continue

        # Create cleaned version without 'claim' field
        cleaned_citation = {k: v for k, v in citation.items() if k != "claim"}

        # Count if we actually removed a claim
        if "claim" in citation:
            claims_removed += 1
            logger.debug(f"Removed claim field from citation")

        cleaned_citations.append(cleaned_citation)

    return cleaned_citations, claims_removed


def clean_team_citations(
    team_relevancy_list: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Remove claim fields from all citations in team relevancy data.

    Returns:
        Tuple of (cleaned_data, statistics)
    """
    if not isinstance(team_relevancy_list, list):
        return team_relevancy_list, {"teams_processed": 0, "claims_removed": 0}

    cleaned_data = []
    stats = {"teams_processed": 0, "claims_removed": 0}

    for team_data in team_relevancy_list:
        if not isinstance(team_data, dict):
            cleaned_data.append(team_data)
            continue

        stats["teams_processed"] += 1
        team_name = team_data.get("team_name", "Unknown")

        # Create cleaned version
        cleaned_team = team_data.copy()

        # Clean citations if they exist
        citations = team_data.get("citations", [])
        if citations:
            cleaned_citations, claims_removed = clean_citation_claims(citations)
            cleaned_team["citations"] = cleaned_citations
            stats["claims_removed"] += claims_removed

            if claims_removed > 0:
                logger.debug(
                    f"Team '{team_name}': Removed {claims_removed} claim fields from citations"
                )

        cleaned_data.append(cleaned_team)

    return cleaned_data, stats


def upgrade() -> None:
    """Data migration: Remove claim fields from existing citations to optimize memory usage."""
    connection = op.get_bind()

    # Get the laws table
    laws_table = sa.table(
        "law_monitoring_laws",
        sa.column("law_id", sa.String),
        sa.column("team_relevancy_classification", sa.JSON),
    )

    logger.info("Starting citation claim field removal migration...")

    # Find all laws with team_relevancy_classification data
    result = connection.execute(
        sa.select(
            laws_table.c.law_id, laws_table.c.team_relevancy_classification
        ).where(laws_table.c.team_relevancy_classification.isnot(None))
    )

    total_stats = {
        "laws_processed": 0,
        "laws_modified": 0,
        "teams_processed": 0,
        "claims_removed": 0,
    }

    for row in result:
        law_id = row.law_id
        team_relevancy_data = row.team_relevancy_classification

        if not team_relevancy_data:
            continue

        total_stats["laws_processed"] += 1

        # Clean the team relevancy data
        cleaned_data, law_stats = clean_team_citations(team_relevancy_data)

        if law_stats["claims_removed"] > 0:
            total_stats["laws_modified"] += 1
            total_stats["teams_processed"] += law_stats["teams_processed"]
            total_stats["claims_removed"] += law_stats["claims_removed"]

            # Update the law with cleaned data
            connection.execute(
                sa.update(laws_table)
                .where(laws_table.c.law_id == law_id)
                .values(team_relevancy_classification=cleaned_data)
            )

            logger.info(
                f"Law {law_id}: Removed {law_stats['claims_removed']} claim fields from citations"
            )

    logger.success(
        f"Migration completed: {total_stats['laws_processed']} laws processed, "
        f"{total_stats['laws_modified']} laws modified, "
        f"{total_stats['claims_removed']} claim fields removed"
    )


def downgrade() -> None:
    """Downgrade: This migration cannot be automatically reversed.

    The claim fields were removed for memory optimization. The original claim data
    was always identical to the team's reasoning field, so no unique data was lost.
    If needed, the claim fields could be regenerated by copying team.reasoning to
    each citation.claim, but this should not be necessary as the claim field was
    redundant and never used independently.
    """
    logger.warning(
        "This data migration cannot be automatically reversed. "
        "The removed claim fields were redundant (identical to team.reasoning). "
        "If needed, claims could be regenerated from team reasoning, but this "
        "would reintroduce the memory waste that this migration was designed to eliminate."
    )
