from pyramid.exceptions import ConfigurationError
from pyramid.security import unauthenticated_userid

from passlib.context import CryptContext

from speak_friend.passwords import PasswordValidator

from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile


def add_controlpanel_section(config, schema, override=False):
    controlpanel = config.registry.setdefault('controlpanel', {})
    if schema.name in controlpanel and not override:
        msg = '%s section already implemented by: %s'
        raise ConfigurationError(msg % (schema.name,
                                        schema.path))
    controlpanel[schema.name] = schema


def set_password_context(config, context=None, ini_string='', ini_file=None,
                         context_dict={}):
    """
    Create a CryptContext used by the application for password management

    One of 'context', 'string', 'ini_file' or 'context_args' must be supplied.

    :arg context:
        A passlib CryptContext object

    :arg ini_string
        A string of configuration data such as that created by
        CryptContext.to_string
        (see http://pythonhosted.org/passlib/lib/passlib.context.html#passlib.context.CryptContext.to_string)

    :arg ini_file:
        Identifies a .ini-style file which contains a [passlib] section
        suitable for constructing a passlib CryptContext
        (see http://pythonhosted.org/passlib/lib/passlib.context.html#passlib.context.CryptContext.to_string)

    :arg context_dict:
        A dictionary of arguments suitable for constructing a CryptContext
        (see http://pythonhosted.org/passlib/lib/passlib.context.html#passlib.context.CryptContext.to_dict)

    :raises ConfigurationError
        If given insufficient or incorrect arguments
    """
    def register_context():
        bad_config = ""
        constructed_context = None
        try:
            if context:
                if isinstance(context, CryptContext):
                    constructed_context = context
                else:
                    msg = "'context' must be an instance of passlib.CryptContext"
                    bad_config = msg
            elif ini_string:
                constructed_context = CryptContext.from_string(ini_string)
            elif ini_file:
                constructed_context = CryptContext.from_path(ini_file)
            elif context_dict:
                constructed_context = CryptContext(**context_dict)
            else:
                # no required arguments have been passed, error
                bad_config = 'requires a CryptContext or configuration data'
        except IOError:
            bad_config = "unable to open %s" % ini_file
        except ValueError:
            bad_config = "received invalid or incompatible configuration options"
        except KeyError:
            bad_config = "received unknown or forbidden configuration options"
        except TypeError:
            bad_config = "received configuration options of the wrong type"

        if bad_config:
            raise ConfigurationError("set_password_context %s" % bad_config)

        config.registry.password_context = constructed_context

    config.action('password_context', register_context)


def set_password_validator(config, validator_class=PasswordValidator):
    def initialize_validator():
        settings = config.registry.settings
        validator = validator_class(settings)
        config.registry.password_validator = validator

    config.action('password_validator', initialize_validator)


def get_user(request):
    userid = unauthenticated_userid(request)
    if userid is not None:
        # this should return None if the user doesn't exist
        # in the database
        session = DBSession()
        return session.query(UserProfile).get(userid)
