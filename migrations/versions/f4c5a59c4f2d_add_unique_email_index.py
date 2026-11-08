"""Add unique email index

Revision ID: f4c5a59c4f2d
Revises: 4d524db999c4
Create Date: 2026-10-21 22:36:28.295083

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4c5a59c4f2d'
down_revision = '4d524db999c4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'ix_user_email',
        'user',
        ['email'],
        unique=True
    )


def downgrade():
    op.drop_index(
        'ix_user_email',
        table_name='user'
    )

    # ### end Alembic commands ###
