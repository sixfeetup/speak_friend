from pyramid.events import NewResponse

from openid.yadis.constants import YADIS_HEADER_NAME

from speak_friend.subscribers import add_yadis_header
from speak_friend.tests.common import SFBaseCase


class SubscriberTests(SFBaseCase):
    def test_xrds_header(self):
        event = NewResponse(self.request, self.request.response)
        add_yadis_header(event)
        self.assertIn(YADIS_HEADER_NAME, event.response.headers)
