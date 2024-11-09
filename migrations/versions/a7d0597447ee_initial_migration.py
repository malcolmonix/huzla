"""Initial migration

Revision ID: a7d0597447ee
Revises: 
Create Date: 2024-11-09 04:05:27.295436

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7d0597447ee'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'state', ['state_id'], ['id'])

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('latitude')
        batch_op.drop_column('longitude')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('longitude', sa.FLOAT(), nullable=True))
        batch_op.add_column(sa.Column('latitude', sa.FLOAT(), nullable=True))

    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('state_id')

    # ### end Alembic commands ###
