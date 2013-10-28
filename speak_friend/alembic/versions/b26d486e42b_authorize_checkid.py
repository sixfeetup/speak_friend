"""authorize_checkid activity

Revision ID: b26d486e42b
Revises: 269a5d4d4573
Create Date: 2013-10-28 15:51:33.786352

"""

# revision identifiers, used by Alembic.
revision = 'b26d486e42b'
down_revision = '269a5d4d4573'

from alembic import op
from sqlalchemy import String
from sqlalchemy import Table, Column, MetaData


activities = Table(
    'activities',
    MetaData(),
    Column('activity', String),
    schema='reports',
)
activities.implicit_returning = False

authorize_checkid = op.inline_literal(u'authorize_checkid')


def upgrade():
    sql = activities.insert()
    op.execute(sql.values({'activity': authorize_checkid}))


def downgrade():
    sql = activities.delete()
    op.execute(sql.values({'activity': authorize_checkid}))
