import logging
import os
import sys
import transaction

from pwgen import pwgen

from pyramid.config import Configurator
from pyramid.paster import get_appsettings, setup_logging

from sqlalchemy.exc import IntegrityError

import transaction

from speak_friend import init_sa
from speak_friend.configuration import set_password_context
from speak_friend.models import Base, DBSession
from speak_friend.models.profiles import UserProfile


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage %s <config_uri> <num_users>\n'
          '(example: "%s development.ini 4000")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 3:
        usage(argv)
    config_uri = argv[1]
    try:
        num_users = int(argv[2])
    except ValueError:
        usage(argv)
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    config = Configurator(settings=settings)
    config.add_directive('set_password_context', set_password_context)
    engine = init_sa(config)
    logger = logging.getLogger('speak_friend.createusers')

    if 'speak_friend.password_hasher' in settings:
        config.include(settings['speak_friend.password_hasher'])
    else:
        from passlib.apps import ldap_context
        config.set_password_context(context=ldap_context)
    # makes the password_context available on the registry
    config.commit()

    pass_ctx = config.registry.password_context
    users_created = []
    user_num = 1
    while len(users_created) < num_users:
        first_name = u'Test'
        last_name = u'User%d' % user_num
        username = u'%s.%s' % (first_name, last_name)
        password = pwgen(num_pw=1, pw_length=20, numerals=True,
                         capitalize=True, no_symbols=True)
        email = u'%s@example.com' % username
        pw_hash = pass_ctx.encrypt(password)

        transaction.begin()

        user = UserProfile(
            username,
            first_name,
            last_name,
            email,
            pw_hash,
            None,
            0,
            False,
            is_superuser=False
        )
        user_num += 1
        try:
            DBSession.add(user)
            transaction.commit()
            logger.info("Created user %s", username)
        except (IntegrityError,), err:
            transaction.abort()
            msg = err.message.split('\n')[1]
            logger.warning('Unable to create user "%s", skipping: %s',
                           username, msg)
            continue

        users_created.append((username, password))

    for uname, pw in users_created:
        print uname, pw
