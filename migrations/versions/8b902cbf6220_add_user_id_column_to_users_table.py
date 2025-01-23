"""Add user_id column to users table

Revision ID: 8b902cbf6220
Revises: b23abde01b88
Create Date: 2024-12-19 21:40:37.172219

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b902cbf6220'
down_revision = 'b23abde01b88'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('representatives', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)  # تغيير إلى nullable=True
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)

    with op.batch_alter_table('supervisors', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)  # تغيير إلى nullable=True
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('user_id')

    with op.batch_alter_table('supervisors', schema=None) as batch_op:
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('representatives', schema=None) as batch_op:
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###
