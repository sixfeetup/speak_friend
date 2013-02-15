from pyramid import testing
from speak_friend.views.accounts import create_profile, edit_profile

from speak_friend.tests.common import SFBaseCase


class ViewTests(SFBaseCase):
    def test_create_profile_view(self):
        request = testing.DummyRequest()
        info = create_profile(request)
        self.assertTrue('form' in info)

    def test_edit_profile_view(self):
        request = testing.DummyRequest()
        info = edit_profile(request)
        self.assertTrue('form' in info)
