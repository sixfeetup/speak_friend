from pyramid.exceptions import ConfigurationError
from pyramid.path import DottedNameResolver


def verify_password_hasher(hasher):
    secret = 'secret'
    try:
        this_hash = hasher.encrypt(secret)
        matches = hasher.verify(secret, this_hash)
    except AttributeError:
        return False
    return matches


def set_password_hash(config, pwhash):
    """
    Set the password hash to be used.
    
    :arg pwhash: 
        * A class implementing the passlib API, 
        * A dotted name which can be resolved to such a class
    
    :raises ConfigurationError
        If a value is supplied which cannot be resolved to a python Class
    """
    resolver = DottedNameResolver(package=None)
    def register_hash():
        try:
            hash_class = resolver.maybe_resolve(pwhash)
            if not verify_password_hasher(hash_class):
                raise ConfigurationError('Does not implement passlib API')
        except ImportError:
            raise ConfigurationError('Unable to resolve name %s' % pwhash)
        else:
            config.registry.password_hash = resolver.maybe_resolve(pwhash)
    config.action('password_hash', register_hash)
