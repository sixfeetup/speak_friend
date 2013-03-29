import os
import sys
import transaction

from pyramid.config import Configurator
from pyramid.paster import get_appsettings, setup_logging

from speak_friend import init_sa
from speak_friend.configuration import set_password_context
from speak_friend.models import Base, DBSession
from speak_friend.models.profiles import UserProfile


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    config = Configurator(settings=settings)
    config.add_directive('set_password_context', set_password_context)
    engine = init_sa(config)

    Base.metadata.create_all(engine)

    if 'speak_friend.admin_username' not in settings:
        print("No admin user name specified. Skipping.")
        sys.exit(0)

    admin_username = settings['speak_friend.admin_username']

    # Don't overwrite the user's info if they're already there.
    if DBSession.query(UserProfile).filter(
        UserProfile.username == admin_username).first():
        print("Admin user already present, skipping creation.")
        sys.exit(0)

    if 'speak_friend.password_hasher' in settings:
        config.include(settings['speak_friend.password_hasher'])
    else:
        from passlib.apps import ldap_context
        config.set_password_context(context=ldap_context)
    # makes the password_context available on the registry
    config.commit()

    pass_ctx = config.registry.password_context
    with transaction.manager:

        admin_password = settings['speak_friend.admin_password']
        admin_email = settings['site_from']
        pw_hash = pass_ctx.encrypt(admin_password)

        model = UserProfile(
            admin_username,
            'OpenID',
            'Admin',
            admin_email,
            pw_hash,
            None,
            0,
            False,
            is_superuser=True
        )

        DBSession.merge(model)
        print("Created admin user %s" % admin_username)
