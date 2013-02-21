import os

from pyramid.exceptions import ConfigurationError
from passlib.context import CryptContext

from speak_friend.tests.common import SFBaseCase

class DummyPasslibContext(object):
    pass
bad_context = DummyPasslibContext()


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INI_FILE_PATH = os.path.join(CURRENT_DIR, 'src', 'good_passlib.ini')
BAD_INI_PATH = os.path.join(CURRENT_DIR, 'src', 'nohash_passlib.ini')
GOOD_DICT = {
    'schemes': ['sha256_crypt', 'ldap_salted_md5'],
    'ldap_salted_md5__salt_size': 16,
    'sha256_crypt__default_rounds': 10000,
}
BAD_DICT = GOOD_DICT.copy()
BAD_DICT['unsupported_keyword'] = 42


class PasswordBaseCase(SFBaseCase):
    def setUp(self):
        super(PasswordBaseCase, self).setUp()
        self.config.include('speak_friend')


class PasswordPluginTests(PasswordBaseCase):
    def assertContextCorrect(self, context):
        self.assertTrue(isinstance(context, CryptContext))
        expected_schemes = ('sha256_crypt', 'ldap_salted_md5')
        actual_schemes = context.schemes()
        self.assertEqual(expected_schemes, actual_schemes)
        
    
    def test_default_context(self):
        from passlib.apps import ldap_context
        self.assertTrue(self.config.registry.password_context is ldap_context)

    def test_bad_context_instance(self):
        self.assertRaises(ConfigurationError,
                          self.config.set_password_context,
                          context=bad_context)

    def test_custom_context(self):
        ctx = CryptContext.from_path(INI_FILE_PATH)
        self.config.set_password_context(context=ctx)
        self.assertTrue(self.config.registry.password_context is ctx)

    def test_context_from_path(self):
        self.config.set_password_context(ini_file=INI_FILE_PATH)
        self.assertContextCorrect(self.config.registry.password_context)

    def test_bad_path(self):
        self.assertRaises(ConfigurationError,
                          self.config.set_password_context,
                          ini_file="/does/not/exist.ini")

    def test_bad_file(self):
        self.assertRaises(ConfigurationError,
                          self.config.set_password_context,
                          ini_file=BAD_INI_PATH)

    def test_context_from_string(self):
        ini_string = ''
        with open(INI_FILE_PATH, 'r') as ini_file:
            ini_string = ini_file.read()
        self.config.set_password_context(ini_string=ini_string)
        self.assertContextCorrect(self.config.registry.password_context)

    def test_bad_string(self):
        ini_string = ''
        with open(BAD_INI_PATH, 'r') as bad_file:
            ini_string = bad_file.read()
        self.assertRaises(ConfigurationError,
                          self.config.set_password_context,
                          ini_string=ini_string)

    def test_context_from_context_dict(self):
        self.config.set_password_context(context_dict=GOOD_DICT)
        self.assertContextCorrect(self.config.registry.password_context)

    def test_bad_dict(self):
        self.assertRaises(ConfigurationError,
                          self.config.set_password_context,
                          context_dict=BAD_DICT)
