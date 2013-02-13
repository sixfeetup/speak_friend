import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.config import aslist
from pyramid.paster import get_appsettings, setup_logging
from pyramid.path import DottedNameResolver

from speak_friend.models import DBSession, Base
from speak_friend.models.openid import Association, Nonce
from speak_friend.models.profiles import UserProfile
from speak_friend.models.controlpanel import ControlPanel


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
    resolver = DottedNameResolver()
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    extra_model_paths = aslist(settings.get('speak_friend.extra_models', []))
    extra_models = {}
    for emp in extra_model_paths:
        extra_models[emp] = resolver.resolve(emp)

    Base.metadata.create_all(engine)
#    with transaction.manager:
#        model = MyModel(name='one', value=1)
#        DBSession.add(model)
