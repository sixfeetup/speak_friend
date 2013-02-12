from pyramid import testing
from speak_friend.views.profiles import CreateProfile, edit_profile

from speak_friend.tests.common import SFBaseCase


class ViewTests(SFBaseCase):
    def test_create_profile_view(self):
        request = testing.DummyRequest()
        view = CreateProfile(request)
        info = view.get()
        self.assertTrue('form' in info)

    def test_edit_profile_view(self):
        request = testing.DummyRequest()
        info = edit_profile(request)
        self.assertTrue('form' in info)
