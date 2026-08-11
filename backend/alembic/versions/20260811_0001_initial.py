"""Initial booking analytics schema."""
from alembic import op
import sqlalchemy as sa

revision = "20260811_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uploads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("booking_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("upload_id", sa.Integer(), sa.ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("booking_reference", sa.String(64), nullable=False, index=True),
        sa.Column("booking_date", sa.Date()),
        sa.Column("travel_date", sa.Date()),
        sa.Column("agent", sa.String(128), index=True),
        sa.Column("team", sa.String(128), index=True),
        sa.Column("source", sa.String(128)),
        sa.Column("selling_cost", sa.Numeric(14, 2)),
        sa.Column("profit", sa.Numeric(14, 2)),
        sa.Column("booking_type", sa.String(128)),
        sa.Column("booking_status", sa.String(64)),
        sa.Column("payment_status", sa.String(128)),
        sa.Column("product_status", sa.String(128), index=True),
        sa.Column("pending_products", sa.Text()),
        sa.Column("special_requests", sa.Text()),
        sa.Column("attachments_status", sa.Text()),
        sa.Column("quality_checks", sa.JSON(), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("upload_id", "booking_reference", name="uq_booking_upload_reference"),
    )
    op.create_table(
        "errors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("upload_id", sa.Integer(), sa.ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("booking_reference", sa.String(64), nullable=False, index=True),
        sa.Column("department", sa.String(128)),
        sa.Column("issue_date", sa.Date(), index=True),
        sa.Column("issue_text", sa.Text(), nullable=False),
        sa.Column("normalized_issue", sa.Text(), nullable=False),
        sa.Column("issue_hash", sa.String(64), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("raw_status", sa.String(128)),
        sa.Column("responsible_agent", sa.String(128), index=True),
        sa.Column("handled_agent", sa.String(128), index=True),
        sa.Column("reported_to", sa.String(128)),
        sa.Column("remarks", sa.Text()),
        sa.Column("action_taken", sa.Text()),
        sa.Column("category", sa.String(128), nullable=False, index=True),
        sa.Column("severity", sa.String(32), nullable=False, index=True),
        sa.Column("ai_category", sa.String(128)),
        sa.Column("ai_subcategory", sa.String(128)),
        sa.Column("ai_severity", sa.String(32)),
        sa.Column("ai_summary", sa.Text()),
        sa.Column("ai_recommended_action", sa.Text()),
        sa.Column("raw_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "error_classifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_hash", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("error_classifications")
    op.drop_table("errors")
    op.drop_table("bookings")
    op.drop_table("uploads")

