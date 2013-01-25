from unittest import TestCase

from pyramid import testing

from .api import TemplateAPI
from .subscribers import register_api
from .views.accounts import create_account


class SFBaseCase(TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.add_settings({'site_name': "Test"})

    def tearDown(self):
        testing.tearDown()


class ViewTests(SFBaseCase):
    def test_create_account_view(self):
        request = testing.DummyRequest()
        info = create_account(request)
        self.assertEqual(len(info.keys()), 0)


class SubscriberTests(SFBaseCase):
    def test_register_api(self):
        event_dict = {}
        register_api(event_dict)
        self.assertTrue('api' in event_dict.keys())


class TemplateAPITests(SFBaseCase):
    def test_settings(self):
        api = TemplateAPI()
        self.assertTrue(hasattr(api, 'settings'))
