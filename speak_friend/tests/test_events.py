from speak_friend.tests.common import SFBaseCase
from speak_friend.tests.mocks import create_user
from speak_friend.events import PasswordReset


class EventTests(SFBaseCase):

    def test_default_password_reset(self):
        user = create_user('dave')
        self.request.referrer = 'http://example.com'
        event = PasswordReset(self.request, user)
        self.assertTrue(event.notify_user)
