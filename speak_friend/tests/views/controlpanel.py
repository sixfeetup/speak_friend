from pyramid import testing
from speak_friend.views.accounts import ControlPanel

from speak_friend.forms.controlpanel import TOKEN_DURATION
from speak_friend.forms.controlpanel import authentication_schema
from speak_friend.tests.common import SFBaseCase
from speak_friend.tests.mocks import MockSession


class ViewTests(SFBaseCase):
    def setUp(self):
        super(ViewTests, self).setUp()
        self.config.include('speak_friend')

    def test_get_value(self):
        request = testing.DummyRequest()
        request.user = None
        request.db_session = MockSession()
        cp = ControlPanel(request)
        authentication_schema
        token_duration = cp.get_value(authentication_schema.name,
                                      'token_duration')
        self.assertTrue(token_duration == TOKEN_DURATION)
