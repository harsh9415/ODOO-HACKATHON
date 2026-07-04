"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
    )

    userrole = postgresql.ENUM("admin", "employee", name="userrole", create_type=False)
    userrole.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("login_id", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("must_change_password", sa.Boolean(), default=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("email_verified", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "employee_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id")),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("department", sa.String(100)),
        sa.Column("manager_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("location", sa.String(100)),
        sa.Column("date_of_joining", sa.Date(), nullable=False),
        sa.Column("profile_picture_url", sa.String(500)),
        sa.Column("dob", sa.Date()),
        sa.Column("residing_address", sa.Text()),
        sa.Column("nationality", sa.String(100)),
        sa.Column("personal_email", sa.String(255)),
        sa.Column("gender", sa.String(20)),
        sa.Column("marital_status", sa.String(20)),
        sa.Column("emp_code", sa.String(50)),
    )

    op.create_table(
        "bank_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("account_number", sa.String(50)),
        sa.Column("bank_name", sa.String(100)),
        sa.Column("ifsc_code", sa.String(20)),
        sa.Column("pan_no", sa.String(20)),
        sa.Column("uan_no", sa.String(20)),
    )

    op.create_table(
        "resume_info",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("about", sa.Text()),
        sa.Column("job_love_note", sa.Text()),
        sa.Column("interests", sa.Text()),
        sa.Column("skills", postgresql.JSON()),
        sa.Column("certifications", postgresql.JSON()),
    )

    op.create_table(
        "salary_structures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("month_wage", sa.Float(), default=0),
        sa.Column("working_days_per_week", sa.Integer(), default=5),
        sa.Column("break_time_minutes", sa.Integer(), default=60),
        sa.Column("basic_pct", sa.Float(), default=50.0),
        sa.Column("hra_pct", sa.Float(), default=50.0),
        sa.Column("standard_allowance_pct", sa.Float(), default=8.33),
        sa.Column("performance_bonus_pct", sa.Float(), default=8.33),
        sa.Column("lta_pct", sa.Float(), default=8.33),
        sa.Column("pf_employee_pct", sa.Float(), default=12.0),
        sa.Column("pf_employer_pct", sa.Float(), default=12.0),
        sa.Column("professional_tax", sa.Float(), default=200.0),
    )

    attendancestatus = postgresql.ENUM(
        "present", "absent", "half-day", "leave", name="attendancestatus", create_type=False
    )
    attendancestatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("check_in", sa.Time()),
        sa.Column("check_out", sa.Time()),
        sa.Column("status", attendancestatus),
    )

    leavetype = postgresql.ENUM("Paid Time Off", "Sick Leave", "Unpaid Leaves", name="leavetype", create_type=False)
    leavetype.create(op.get_bind(), checkfirst=True)
    leavestatus = postgresql.ENUM("Pending", "Approved", "Rejected", name="leavestatus", create_type=False)
    leavestatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column("leave_type", leavetype, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("remarks", sa.Text()),
        sa.Column("status", leavestatus),
        sa.Column("attachment_url", sa.String(500), nullable=True),
        sa.Column("admin_comment", sa.Text()),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50)),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("leave_requests")
    op.drop_table("attendance")
    op.drop_table("salary_structures")
    op.drop_table("resume_info")
    op.drop_table("bank_details")
    op.drop_table("employee_profiles")
    op.drop_table("users")
    op.drop_table("companies")
    op.execute("DROP TYPE IF EXISTS leavestatus")
    op.execute("DROP TYPE IF EXISTS leavetype")
    op.execute("DROP TYPE IF EXISTS attendancestatus")
    op.execute("DROP TYPE IF EXISTS userrole")
