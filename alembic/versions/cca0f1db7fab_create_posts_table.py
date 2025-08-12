"""create posts table

Revision ID: cca0f1db7fab
Revises:
Create Date: 2025-08-11 18:40:27.327905

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cca0f1db7fab"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer, nullable=False, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.String(255), nullable=False),
        sa.Column(
            "published", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column("rating", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("posts")
