from speak_friend.api import TemplateAPI
from speak_friend.tests.common import SFBaseCase


class TemplateAPITests(SFBaseCase):
    def test_settings(self):
        api = TemplateAPI()
        self.assertTrue(hasattr(api, 'settings'))
