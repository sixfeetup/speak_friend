from pyramid import testing

from speak_friend.api import TemplateAPI
from speak_friend.tests.common import SFBaseCase


class TemplateAPITests(SFBaseCase):
    def setUp(self):
        super(TemplateAPITests, self).setUp()
        self.api = TemplateAPI(testing.DummyRequest(), {})

    def test_settings(self):
        self.assertTrue(hasattr(self.api, 'settings'))

    def test_macros(self):
        self.assertTrue(hasattr(self.api, 'macros'))

    def test_resources(self):
        self.assertTrue(hasattr(self.api, 'css_resources'))
        self.assertTrue(hasattr(self.api, 'js_resources'))

    def test_current_year(self):
        self.assertTrue(hasattr(self.api, 'utc_now'))
