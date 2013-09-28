import os
import sys

import transaction

from sixfeetup.bowab.scripts.initializedb import main as bowab_main

from speak_friend.models.profiles import UserProfile


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    env = bowab_main(argv)
    settings = env['registry'].settings
    db_session = env['registry']['bowab.db_session']

    if 'speak_friend.admin_username' not in settings:
        print("No admin user name specified. Skipping.")
        sys.exit(0)

    admin_username = settings['speak_friend.admin_username']

    # Don't overwrite the user's info if they're already there.
    if db_session.query(UserProfile).filter(
        UserProfile.username == admin_username).first():
        print("Admin user already present, skipping creation.")
        sys.exit(0)

    pass_ctx = env['registry'].password_context
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
