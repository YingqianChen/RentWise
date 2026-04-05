"""add candidate sdu hint fields"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0002"
down_revision = "20260402_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidate_extracted_info", sa.Column("suspected_sdu", sa.Boolean(), nullable=True))
    op.add_column("candidate_extracted_info", sa.Column("sdu_detection_reason", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate_extracted_info", "sdu_detection_reason")
    op.drop_column("candidate_extracted_info", "suspected_sdu")
