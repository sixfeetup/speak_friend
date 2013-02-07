from unittest import TestCase

from pyramid import testing
from pyramid.exceptions import ConfigurationError

from .api import TemplateAPI
from .forms import profiles
from .subscribers import register_api
from .views.accounts import create_profile, edit_profile


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


class SFBaseCase(TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.add_settings({'site_name': "Test"})
        self.config.include('speak_friend')

    def tearDown(self):
        testing.tearDown()


class ViewTests(SFBaseCase):
    def test_create_profile_view(self):
        request = testing.DummyRequest()
        info = create_profile(request)
        self.assertTrue('form' in info)

    def test_edit_profile_view(self):
        request = testing.DummyRequest()
        info = edit_profile(request)
        self.assertTrue('form' in info)


class SubscriberTests(SFBaseCase):
    def test_register_api(self):
        event_dict = {}
        register_api(event_dict)
        self.assertTrue('api' in event_dict.keys())


class TemplateAPITests(SFBaseCase):
    def test_settings(self):
        api = TemplateAPI()
        self.assertTrue(hasattr(api, 'settings'))


class FormTests(TestCase):
    def test_profile_form_policy_title(self):
        self.assertEqual(profiles.profile_form['agree_to_policy'].title,
                         'I agree to the usage policy.')

    def test_profile_form_email_fields(self):
        self.assertEqual(profiles.profile_form['password'].widget.__class__.__name__,
                         'CheckedPasswordWidget')

    def test_profile_form_password_fields(self):
        self.assertEqual(profiles.profile_form['email'].widget.__class__.__name__,
                         'CheckedInputWidget')


class PasswordPluginTests(SFBaseCase):
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
