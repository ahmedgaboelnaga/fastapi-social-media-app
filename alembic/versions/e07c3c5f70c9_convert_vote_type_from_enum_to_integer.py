"""convert vote type from enum to integer

Revision ID: e07c3c5f70c9
Revises: 5e61a672b7d7
Create Date: 2025-12-28 01:51:20.564650

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e07c3c5f70c9"
down_revision: Union[str, Sequence[str], None] = "5e61a672b7d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add temporary integer column
    op.add_column("votes", sa.Column("type_int", sa.Integer(), nullable=True))

    # Step 2: Convert existing data: 'upvote' -> 1, 'downvote' -> 2
    op.execute("""
        UPDATE votes 
        SET type_int = CASE 
            WHEN type::text = 'upvote' THEN 1
            WHEN type::text = 'downvote' THEN 2
        END
    """)

    # Step 3: Make the new column NOT NULL
    op.alter_column("votes", "type_int", nullable=False)

    # Step 4: Drop old enum column
    op.drop_column("votes", "type")

    # Step 5: Rename new column to 'type'
    op.alter_column("votes", "type_int", new_column_name="type")

    # Step 6: Drop the enum type (if no other tables use it)
    op.execute("DROP TYPE IF EXISTS votetype")


def downgrade() -> None:
    """Downgrade schema."""
    # Step 1: Recreate the enum type
    votetype = postgresql.ENUM("upvote", "downvote", name="votetype")
    votetype.create(op.get_bind())

    # Step 2: Add temporary enum column
    op.add_column("votes", sa.Column("type_enum", votetype, nullable=True))

    # Step 3: Convert integers back to enums: 1 -> 'upvote', 2 -> 'downvote'
    op.execute("""
        UPDATE votes 
        SET type_enum = CASE 
            WHEN type = 1 THEN 'upvote'::votetype
            WHEN type = 2 THEN 'downvote'::votetype
        END
    """)

    # Step 4: Make the enum column NOT NULL
    op.alter_column("votes", "type_enum", nullable=False)

    # Step 5: Drop integer column
    op.drop_column("votes", "type")

    # Step 6: Rename enum column to 'type'
    op.alter_column("votes", "type_enum", new_column_name="type")
