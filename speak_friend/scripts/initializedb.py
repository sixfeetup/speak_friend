import os
import sys

import transaction

from sixfeetup.bowab.scripts.initializedb import main as bowab_main

from speak_friend.configuration import set_password_context
from speak_friend.configuration import set_username_validator
from speak_friend.models.profiles import UserProfile


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    config, db_session = bowab_main(argv)
    settings = config.registry.settings

    config.add_directive('set_password_context', set_password_context)
    config.add_directive('set_username_validator', set_username_validator)
    if 'speak_friend.admin_username' not in settings:
        print("No admin user name specified. Skipping.")
        sys.exit(0)

    admin_username = settings['speak_friend.admin_username']

    # Don't overwrite the user's info if they're already there.
    if db_session.query(UserProfile).filter(
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

        db_session.merge(model)
        print("Created admin user %s" % admin_username)
