"""Add decision signals to candidate extracted info.

Revision ID: 20260406_0005
Revises: 20260405_0004_candidate_processing_fields
Create Date: 2026-04-06 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260406_0005"
down_revision = "20260405_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_extracted_info",
        sa.Column(
            "decision_signals",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("candidate_extracted_info", "decision_signals")
