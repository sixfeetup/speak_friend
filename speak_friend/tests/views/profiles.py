from pyramid import testing
from webob.multidict import MultiDict
from speak_friend.views.accounts import CreateProfile, EditProfile

from mock import patch

from speak_friend.tests.common import SFBaseCase
from speak_friend.tests.mocks import create_user, MockSession


class DummyPasswordContext(object):
    def __init__(self):
        pass

    def verify(self, password, pw_hash):
        pass


class ViewTests(SFBaseCase):
    def setUp(self):
        super(ViewTests, self).setUp()
        self.config.registry.password_context = DummyPasswordContext()

    def test_create_profile_view_get(self):
        request = testing.DummyRequest()
        request.referrer = '/'
        view = CreateProfile(request)
        info = view.get()
        self.assertTrue('rendered_form' in info)

    def test_create_profile_view_get_on_post(self):
        request = testing.DummyRequest()
        request.referrer = '/'
        view = CreateProfile(request)
        info = view.post()
        self.assertEqual(info.status_code, 405)

    def test_create_profile_view_post_no_args(self):
        request = testing.DummyRequest(post={})
        request.referrer = '/'
        view = CreateProfile(request)
        info = view.post()
        self.assertTrue('rendered_form' in info)

    def test_create_profile_view_submit_empty_form(self):
        request = testing.DummyRequest(post={'submit': ''})
        view = CreateProfile(request)
        info = view.post()
        self.assertTrue('rendered_form' in info)

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
        with patch('speak_friend.forms.profiles.DBSession',
                    new_callable=MockSession):
            info = view.post()
        self.assertTrue('form' not in info.keys())

    def test_edit_profile_view(self):
        request = testing.DummyRequest(path="/edit_profile/testuser")
        request.matchdict['username'] = 'testuser'
        view = EditProfile(request)
        user = create_user('test')
        view.session = MockSession(store=[user])
        view.target_username = 'test'
        view.current_username = 'test'
        with patch('speak_friend.forms.profiles.DBSession',
                    new_callable=MockSession):
            info = view.get()
        print(info)
        self.assertTrue('rendered_form' in info)
