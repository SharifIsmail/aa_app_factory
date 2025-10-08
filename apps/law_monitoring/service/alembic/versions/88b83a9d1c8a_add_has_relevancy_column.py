"""Add has_relevancy boolean column and backfill:
- Only touch rows with status='PROCESSED' to avoid misleading values for unprocessed laws.
- Set has_relevancy=TRUE if any team classification has is_relevant==true.
- Set has_relevancy=FALSE for other PROCESSED rows (no relevant teams).
- Leave has_relevancy=NULL for non-PROCESSED rows.```

Revision ID: 88b83a9d1c8a
Revises: 2641f1afb993
Create Date: 2025-09-19 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.sql import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "88b83a9d1c8a"
down_revision: Union[str, None] = "2641f1afb993"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Table name from ORM: DATABASE_TABLE_PREFIX + "laws" => law_monitoring_laws
    table_name = "law_monitoring_laws"

    # 1) Add column nullable; leave unset (NULL) for non-processed rows
    op.add_column(
        table_name,
        sa.Column("has_relevancy", sa.Boolean(), nullable=True),
    )

    # 2) Backfill only for PROCESSED laws
    bind = op.get_bind()
    # Set TRUE when any item relevant
    backfill_true_sql = text(
        """
        UPDATE law_monitoring_laws AS l
        SET has_relevancy = TRUE
        WHERE l.status = 'PROCESSED' AND EXISTS (
            SELECT 1
            FROM jsonb_array_elements(COALESCE(l.team_relevancy_classification::jsonb, '[]'::jsonb)) AS elem
            WHERE (elem ->> 'is_relevant')::boolean = TRUE
        )
        """
    )
    bind.execute(backfill_true_sql)

    # Set FALSE for other PROCESSED rows (no relevant teams)
    backfill_false_sql = text(
        """
        UPDATE law_monitoring_laws AS l
        SET has_relevancy = FALSE
        WHERE l.status = 'PROCESSED' AND (
            NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements(COALESCE(l.team_relevancy_classification::jsonb, '[]'::jsonb)) AS elem
                WHERE (elem ->> 'is_relevant')::boolean = TRUE
            )
        )
        """
    )
    bind.execute(backfill_false_sql)

    # 3) Optional: keep server default for future inserts; no change needed


def downgrade() -> None:
    table_name = "law_monitoring_laws"
    op.drop_column(table_name, "has_relevancy")
