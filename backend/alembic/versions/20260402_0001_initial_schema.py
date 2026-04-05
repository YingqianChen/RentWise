"""initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260402_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "search_projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("max_budget", sa.Integer(), nullable=True),
        sa.Column("preferred_districts", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("must_have", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("deal_breakers", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("move_in_target", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_search_projects_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_search_projects"),
    )
    op.create_index("ix_search_projects_status", "search_projects", ["status"], unique=False)
    op.create_index("ix_search_projects_user_id", "search_projects", ["user_id"], unique=False)

    op.create_table(
        "candidate_listings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("raw_listing_text", sa.Text(), nullable=True),
        sa.Column("raw_chat_text", sa.Text(), nullable=True),
        sa.Column("raw_note_text", sa.Text(), nullable=True),
        sa.Column("combined_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("user_decision", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["search_projects.id"], name="fk_candidate_listings_project_id_search_projects", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_candidate_listings"),
    )
    op.create_index("ix_candidate_listings_project_id", "candidate_listings", ["project_id"], unique=False)
    op.create_index("ix_candidate_listings_status", "candidate_listings", ["status"], unique=False)
    op.create_index("ix_candidate_listings_user_decision", "candidate_listings", ["user_decision"], unique=False)

    op.create_table(
        "candidate_extracted_info",
        sa.Column("candidate_id", sa.UUID(), nullable=False),
        sa.Column("monthly_rent", sa.String(length=100), nullable=True),
        sa.Column("management_fee_amount", sa.String(length=100), nullable=True),
        sa.Column("management_fee_included", sa.Boolean(), nullable=True),
        sa.Column("rates_amount", sa.String(length=100), nullable=True),
        sa.Column("rates_included", sa.Boolean(), nullable=True),
        sa.Column("deposit", sa.String(length=100), nullable=True),
        sa.Column("agent_fee", sa.String(length=100), nullable=True),
        sa.Column("lease_term", sa.String(length=100), nullable=True),
        sa.Column("move_in_date", sa.String(length=100), nullable=True),
        sa.Column("repair_responsibility", sa.String(length=255), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("furnished", sa.String(length=255), nullable=True),
        sa.Column("size_sqft", sa.String(length=50), nullable=True),
        sa.Column("bedrooms", sa.String(length=50), nullable=True),
        sa.Column("ocr_texts", postgresql.ARRAY(sa.String()), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidate_listings.id"], name="fk_candidate_extracted_info_candidate_id_candidate_listings", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("candidate_id", name="pk_candidate_extracted_info"),
    )

    op.create_table(
        "candidate_cost_assessments",
        sa.Column("candidate_id", sa.UUID(), nullable=False),
        sa.Column("known_monthly_cost", sa.Float(), nullable=True),
        sa.Column("monthly_cost_confidence", sa.String(length=50), nullable=False),
        sa.Column("monthly_cost_missing_items", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("move_in_cost_known_part", sa.Float(), nullable=True),
        sa.Column("move_in_cost_confidence", sa.String(length=50), nullable=False),
        sa.Column("cost_risk_flag", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidate_listings.id"], name="fk_candidate_cost_assessments_candidate_id_candidate_listings", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("candidate_id", name="pk_candidate_cost_assessments"),
    )

    op.create_table(
        "candidate_clause_assessments",
        sa.Column("candidate_id", sa.UUID(), nullable=False),
        sa.Column("repair_responsibility_level", sa.String(length=50), nullable=False),
        sa.Column("lease_term_level", sa.String(length=50), nullable=False),
        sa.Column("move_in_date_level", sa.String(length=50), nullable=False),
        sa.Column("clause_confidence", sa.String(length=50), nullable=False),
        sa.Column("clause_risk_flag", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidate_listings.id"], name="fk_candidate_clause_assessments_candidate_id_candidate_listings", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("candidate_id", name="pk_candidate_clause_assessments"),
    )

    op.create_table(
        "candidate_assessments",
        sa.Column("candidate_id", sa.UUID(), nullable=False),
        sa.Column("potential_value_level", sa.String(length=50), nullable=False),
        sa.Column("completeness_level", sa.String(length=50), nullable=False),
        sa.Column("critical_uncertainty_level", sa.String(length=50), nullable=False),
        sa.Column("decision_risk_level", sa.String(length=50), nullable=False),
        sa.Column("information_gain_level", sa.String(length=50), nullable=False),
        sa.Column("recommendation_confidence", sa.String(length=50), nullable=False),
        sa.Column("next_best_action", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidate_listings.id"], name="fk_candidate_assessments_candidate_id_candidate_listings", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("candidate_id", name="pk_candidate_assessments"),
    )

    op.create_table(
        "investigation_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("candidate_id", sa.UUID(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidate_listings.id"], name="fk_investigation_items_candidate_id_candidate_listings", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["search_projects.id"], name="fk_investigation_items_project_id_search_projects", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_investigation_items"),
    )
    op.create_index("ix_investigation_items_candidate_id", "investigation_items", ["candidate_id"], unique=False)
    op.create_index("ix_investigation_items_project_id", "investigation_items", ["project_id"], unique=False)
    op.create_index("ix_investigation_items_status", "investigation_items", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_investigation_items_status", table_name="investigation_items")
    op.drop_index("ix_investigation_items_project_id", table_name="investigation_items")
    op.drop_index("ix_investigation_items_candidate_id", table_name="investigation_items")
    op.drop_table("investigation_items")
    op.drop_table("candidate_assessments")
    op.drop_table("candidate_clause_assessments")
    op.drop_table("candidate_cost_assessments")
    op.drop_table("candidate_extracted_info")
    op.drop_index("ix_candidate_listings_user_decision", table_name="candidate_listings")
    op.drop_index("ix_candidate_listings_status", table_name="candidate_listings")
    op.drop_index("ix_candidate_listings_project_id", table_name="candidate_listings")
    op.drop_table("candidate_listings")
    op.drop_index("ix_search_projects_user_id", table_name="search_projects")
    op.drop_index("ix_search_projects_status", table_name="search_projects")
    op.drop_table("search_projects")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
