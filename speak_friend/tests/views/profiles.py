from pyramid import testing
from webob.multidict import MultiDict
from speak_friend.views.profiles import CreateProfile, edit_profile

from speak_friend.tests.common import SFBaseCase


class ViewTests(SFBaseCase):
    def test_create_profile_view_get(self):
        request = testing.DummyRequest()
        view = CreateProfile(request)
        info = view.get()
        self.assertTrue('form' in info)

    def test_create_profile_view_get_on_post(self):
        request = testing.DummyRequest()
        view = CreateProfile(request)
        info = view.post()
        self.assertEqual(info.status_code, 405)

    def test_create_profile_view_post_no_args(self):
        request = testing.DummyRequest(post={})
        view = CreateProfile(request)
        info = view.post()
        self.assertTrue('form' in info)

    def test_create_profile_view_submit_empty_form(self):
        request = testing.DummyRequest(post={'submit': ''})
        view = CreateProfile(request)
        info = view.post()
        self.assertTrue('form' in info)
        self.assertTrue('errorMsg' in info['form'])

    def test_create_profile_all_fields(self):
        data = MultiDict([
            ('_charset_', u'UTF-8'),
            ('__formid__', u'deform'),
            ('username', u'myuser'),
            ('first_name', u'Test'),
            ('last_name', u'Testington'),
            ('__start__', u'email:mapping'),
            ('email', u'testing@test.com'),
            ('email-confirm', u'testing@test.com'),
            ('__end__', u'email:mapping'),
            ('__start__', u'password:mapping'),
            ('password', u'aaaaaaaaaaa'),
            ('password-confirm', u'aaaaaaaaaaa'),
            ('__end__', u'password:mapping'),
            ('agree_to_policy', u'true'),
            ('captcha', u'x5J780'),
            ('submit', u'submit'),
        ])
        request = testing.DummyRequest(post=data)
        view = CreateProfile(request)
        info = view.post()
        self.assertEqual(info['form'], None)


    def test_edit_profile_view(self):
        request = testing.DummyRequest()
        info = edit_profile(request)
        self.assertTrue('form' in info)
