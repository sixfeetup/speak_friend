from pyramid.exceptions import ConfigurationError

from speak_friend.tests.common import SFBaseCase

class DummyPasslibClass(object):
    
    @classmethod
    def encrypt(cls, secret):
        return secret[::-1]

    @classmethod
    def verify(cls, secret, myhash):
        return secret == myhash[::-1]


class BadPasslibClass1(object):
    """does not implement the interface"""
    pass


class BadPasslibClass2(DummyPasslibClass):
    """implements the interface incorrectly"""
    @classmethod
    def verify(cls, secret, myhash):
        return False


class PasswordBaseCase(SFBaseCase):
    def setUp(self):
        super(PasswordBaseCase, self).setUp()
        self.config.include('speak_friend')


class PasswordPluginTests(PasswordBaseCase):
    def test_set_password_hash_bad_dotted_name(self):
        self.assertRaises(ConfigurationError,
                          self.config.set_password_hash,
                          'spongecake')

    def test_set_password_hash_dotted_name(self):
        self.config.set_password_hash('passlib.hash.bcrypt')
        from passlib.hash import bcrypt
        self.assertEqual(bcrypt, self.config.registry.password_hash)

    def test_set_password_hash_class(self):
        from passlib.hash import bcrypt
        self.config.set_password_hash(bcrypt)
        self.assertEqual(bcrypt, self.config.registry.password_hash)

    def test_set_password_custom_class(self):
        self.config.set_password_hash(DummyPasslibClass)
        self.assertEqual(DummyPasslibClass,
                         self.config.registry.password_hash)

    def test_set_password_bad_custom_class(self):
        self.assertRaises(ConfigurationError,
                          self.config.set_password_hash,
                          BadPasslibClass1)
        self.assertRaises(ConfigurationError,
                          self.config.set_password_hash,
                          BadPasslibClass2)
