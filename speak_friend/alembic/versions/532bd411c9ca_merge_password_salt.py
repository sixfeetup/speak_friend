"""Merge password salt

Revision ID: 532bd411c9ca
Revises: b26d486e42b
Create Date: 2014-02-10 10:03:04.039430

"""

# revision identifiers, used by Alembic.
revision = '532bd411c9ca'
down_revision = 'b26d486e42b'

from alembic import op
from alembic import context
import sqlalchemy as sa

from pyramid import paster

from speak_friend.models import profiles


def upgrade():
    bind = op.get_bind()
    session = sa.orm.sessionmaker(bind=bind)()
    query = session.query(profiles.UserProfile)

    pyramid_env = paster.bootstrap(context.config.config_file_name)
    pass_ctx = pyramid_env['registry'].password_context

    for profile in query.filter(
            profiles.UserProfile.password_salt != sa.null()):
        scheme = pass_ctx.identify(profile.password_hash)
        # Only sfid_old should have a separate salt
        if scheme != 'sfid_old':
            profile.password_salt = None
            session.add(profile)

    session.commit()


def downgrade():
    pass
