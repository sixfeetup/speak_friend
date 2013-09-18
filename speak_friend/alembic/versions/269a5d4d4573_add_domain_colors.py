"""add domain colors

Revision ID: 269a5d4d4573
Revises: 10ac83d5a9fc
Create Date: 2013-09-18 15:44:31.006887

"""

# revision identifiers, used by Alembic.
revision = '269a5d4d4573'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('domain_profiles', sa.Column('primary_color', sa.UnicodeText, nullable=True), schema="profiles")
    op.add_column('domain_profiles', sa.Column('secondary_color', sa.UnicodeText, nullable=True), schema="profiles")
    ### end Alembic commands ###


def downgrade():
    op.drop_column('domain_profiles', 'primary_color', schema='profiles')
    op.drop_column('domain_profiles', 'secondary_color', schema='profiles')
    ### end Alembic commands ###
