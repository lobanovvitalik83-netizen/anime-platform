"""initial schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-03-27 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admins")),
        sa.UniqueConstraint("username", name=op.f("uq_admins_username")),
    )
    op.create_index("ix_admins_username", "admins", ["username"], unique=False)
    op.create_index("ix_admins_is_active", "admins", ["is_active"], unique=False)

    op.create_table(
        "media_titles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("original_title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_titles")),
    )
    op.create_index("ix_media_titles_type", "media_titles", ["type"], unique=False)
    op.create_index("ix_media_titles_status", "media_titles", ["status"], unique=False)
    op.create_index("ix_media_titles_title", "media_titles", ["title"], unique=False)

    op.create_table(
        "media_seasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title_id", sa.Integer(), nullable=False),
        sa.Column("season_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["title_id"], ["media_titles.id"], name=op.f("fk_media_seasons_title_id_media_titles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_seasons")),
        sa.UniqueConstraint("title_id", "season_number", name="uq_media_seasons_title_season_number"),
    )
    op.create_index("ix_media_seasons_title_id", "media_seasons", ["title_id"], unique=False)

    op.create_table(
        "media_episodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=True),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["season_id"], ["media_seasons.id"], name=op.f("fk_media_episodes_season_id_media_seasons"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["title_id"], ["media_titles.id"], name=op.f("fk_media_episodes_title_id_media_titles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_episodes")),
        sa.UniqueConstraint("season_id", "episode_number", name="uq_media_episodes_season_episode_number"),
    )
    op.create_index("ix_media_episodes_title_id", "media_episodes", ["title_id"], unique=False)
    op.create_index("ix_media_episodes_season_id", "media_episodes", ["season_id"], unique=False)
    op.create_index("ix_media_episodes_status", "media_episodes", ["status"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], name=op.f("fk_audit_logs_admin_id_admins"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index("ix_audit_logs_admin_id", "audit_logs", ["admin_id"], unique=False)
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)

    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("success_rows", sa.Integer(), nullable=False),
        sa.Column("failed_rows", sa.Integer(), nullable=False),
        sa.Column("report_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], name=op.f("fk_import_jobs_admin_id_admins"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_jobs")),
    )
    op.create_index("ix_import_jobs_admin_id", "import_jobs", ["admin_id"], unique=False)
    op.create_index("ix_import_jobs_status", "import_jobs", ["status"], unique=False)

    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title_id", sa.Integer(), nullable=True),
        sa.Column("season_id", sa.Integer(), nullable=True),
        sa.Column("episode_id", sa.Integer(), nullable=True),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("storage_kind", sa.String(length=50), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=255), nullable=True),
        sa.Column("external_url", sa.String(length=2048), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(CASE WHEN title_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN season_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN episode_id IS NOT NULL THEN 1 ELSE 0 END) >= 1",
            name="media_assets_at_least_one_owner",
        ),
        sa.CheckConstraint(
            "(storage_kind = 'telegram_file_id' AND telegram_file_id IS NOT NULL) OR "
            "(storage_kind = 'external_url' AND external_url IS NOT NULL)",
            name="media_assets_storage_kind_payload_match",
        ),
        sa.ForeignKeyConstraint(["episode_id"], ["media_episodes.id"], name=op.f("fk_media_assets_episode_id_media_episodes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["season_id"], ["media_seasons.id"], name=op.f("fk_media_assets_season_id_media_seasons"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["title_id"], ["media_titles.id"], name=op.f("fk_media_assets_title_id_media_titles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_assets")),
    )
    op.create_index("ix_media_assets_title_id", "media_assets", ["title_id"], unique=False)
    op.create_index("ix_media_assets_season_id", "media_assets", ["season_id"], unique=False)
    op.create_index("ix_media_assets_episode_id", "media_assets", ["episode_id"], unique=False)
    op.create_index("ix_media_assets_asset_type", "media_assets", ["asset_type"], unique=False)
    op.create_index("ix_media_assets_is_primary", "media_assets", ["is_primary"], unique=False)

    op.create_table(
        "access_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title_id", sa.Integer(), nullable=True),
        sa.Column("season_id", sa.Integer(), nullable=True),
        sa.Column("episode_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["admins.id"], name=op.f("fk_access_codes_created_by_admin_id_admins"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["episode_id"], ["media_episodes.id"], name=op.f("fk_access_codes_episode_id_media_episodes"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["season_id"], ["media_seasons.id"], name=op.f("fk_access_codes_season_id_media_seasons"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["title_id"], ["media_titles.id"], name=op.f("fk_access_codes_title_id_media_titles"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_access_codes")),
        sa.UniqueConstraint("code", name=op.f("uq_access_codes_code")),
    )
    op.create_index("ix_access_codes_code", "access_codes", ["code"], unique=True)
    op.create_index("ix_access_codes_status", "access_codes", ["status"], unique=False)
    op.create_index("ix_access_codes_title_id", "access_codes", ["title_id"], unique=False)
    op.create_index("ix_access_codes_season_id", "access_codes", ["season_id"], unique=False)
    op.create_index("ix_access_codes_episode_id", "access_codes", ["episode_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_access_codes_episode_id", table_name="access_codes")
    op.drop_index("ix_access_codes_season_id", table_name="access_codes")
    op.drop_index("ix_access_codes_title_id", table_name="access_codes")
    op.drop_index("ix_access_codes_status", table_name="access_codes")
    op.drop_index("ix_access_codes_code", table_name="access_codes")
    op.drop_table("access_codes")

    op.drop_index("ix_media_assets_is_primary", table_name="media_assets")
    op.drop_index("ix_media_assets_asset_type", table_name="media_assets")
    op.drop_index("ix_media_assets_episode_id", table_name="media_assets")
    op.drop_index("ix_media_assets_season_id", table_name="media_assets")
    op.drop_index("ix_media_assets_title_id", table_name="media_assets")
    op.drop_table("media_assets")

    op.drop_index("ix_import_jobs_status", table_name="import_jobs")
    op.drop_index("ix_import_jobs_admin_id", table_name="import_jobs")
    op.drop_table("import_jobs")

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_admin_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_media_episodes_status", table_name="media_episodes")
    op.drop_index("ix_media_episodes_season_id", table_name="media_episodes")
    op.drop_index("ix_media_episodes_title_id", table_name="media_episodes")
    op.drop_table("media_episodes")

    op.drop_index("ix_media_seasons_title_id", table_name="media_seasons")
    op.drop_table("media_seasons")

    op.drop_index("ix_media_titles_title", table_name="media_titles")
    op.drop_index("ix_media_titles_status", table_name="media_titles")
    op.drop_index("ix_media_titles_type", table_name="media_titles")
    op.drop_table("media_titles")

    op.drop_index("ix_admins_is_active", table_name="admins")
    op.drop_index("ix_admins_username", table_name="admins")
    op.drop_table("admins")
