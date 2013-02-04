from unittest import TestCase

from pyramid import testing

from .api import TemplateAPI
from .forms import profiles
from .subscribers import register_api
from .models.openid import SFOpenIDStore
from .views.accounts import create_profile, edit_profile


class SFBaseCase(TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.add_settings({'site_name': "Test"})

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


class OpenIDStoreTest(TestCase):
    def test_method_presence(self):
        store = SFOpenIDStore()
        self.assertTrue(hasattr(store, 'storeAssociation'))
        self.assertTrue(hasattr(store, 'getAssociation'))
        self.assertTrue(hasattr(store, 'removeAssociation'))
        self.assertTrue(hasattr(store, 'useNonce'))
