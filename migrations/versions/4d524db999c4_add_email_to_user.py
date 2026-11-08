"""Add email to User

Revision ID: 4d524db999c4
Revises: a038fdf7ec69
Create Date: 2026-10-21 13:59:01.683145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d524db999c4'
down_revision = 'a038fdf7ec69'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column('email', sa.String(length=255), nullable=True)
    )


def downgrade():
    op.drop_column('user', 'email')

    # ### end Alembic commands ###
