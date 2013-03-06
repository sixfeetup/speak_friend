import os
import sys
import transaction

from pyramid.config import Configurator
from pyramid.paster import get_appsettings, setup_logging

from speak_friend.models import DBSession
from speak_friend.models.profile import UserProfile

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 7:
        usage(argv)
    config_uri = argv[1]
    username = argv[2]
    first_name = argv[3]
    last_name = argv[4]
    email = argv[5]
    password = argv[6]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    config = Configurator(settings=settings)

    pass_ctx = config.registry.password_context
    password_hash = pass_ctx.encrypt(password)

    with transaction.manager:
        user = UserProfile(username,
                           first_name,
                           last_name,
                           email,
                           password_hash,
                           '',
                           0,
                           False,
                           is_superuser=True
        )

        DBSession.add(user)
