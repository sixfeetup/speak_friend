from pyramid.request import Request
from pyramid import testing
from pyramid.events import BeforeRender

from speak_friend.subscribers import register_api
from speak_friend.tests.common import SFBaseCase


class SubscriberTests(SFBaseCase):
    def test_register_api(self):
        event_dict = {
            'request': testing.DummyRequest(),
        }
        event = BeforeRender(event_dict)
        event.rendering_val = {}
        register_api(event)
        self.assertTrue('api' in event)
