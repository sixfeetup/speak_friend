from speak_friend.subscribers import register_api
from speak_friend.tests.common import SFBaseCase


class SubscriberTests(SFBaseCase):
    def test_register_api(self):
        event_dict = {}
        register_api(event_dict)
        self.assertTrue('api' in event_dict.keys())
