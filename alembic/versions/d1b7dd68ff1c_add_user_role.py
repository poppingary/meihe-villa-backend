"""add_user_role

Revision ID: d1b7dd68ff1c
Revises: 2a1a90ef3813
Create Date: 2026-01-27 03:30:22.484684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1b7dd68ff1c'
down_revision: Union[str, None] = '2a1a90ef3813'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    userrole = sa.Enum('ADMIN', 'SUPERADMIN', name='userrole')
    userrole.create(op.get_bind(), checkfirst=True)

    # Add column with default value for existing rows
    op.add_column('users', sa.Column('role', userrole, nullable=False, server_default='ADMIN'))

    # Set poppingary as superadmin
    op.execute("UPDATE users SET role = 'SUPERADMIN' WHERE email = 'poppingary@gmail.com'")

    # Remove server default after migration
    op.alter_column('users', 'role', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'role')
    # Drop the enum type
    sa.Enum('ADMIN', 'SUPERADMIN', name='userrole').drop(op.get_bind(), checkfirst=True)
