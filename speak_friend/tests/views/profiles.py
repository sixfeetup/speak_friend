from pyramid import testing
from webob.multidict import MultiDict
from speak_friend.views.accounts import CreateProfile, EditProfile

from mock import patch

from sixfeetup.bowab.tests.mocks import MockSession

from speak_friend.forms.controlpanel import MAX_DOMAIN_ATTEMPTS
from speak_friend.tests.common import SFBaseCase
from speak_friend.tests.mocks import create_user


class DummyPasswordContext(object):
    def __init__(self):
        pass

    def verify(self, password, pw_hash):
        pass


class ViewTests(SFBaseCase):
    def setUp(self):
        super(ViewTests, self).setUp()
        self.config.registry.password_context = DummyPasswordContext()
        self.config.add_route('contact_us', '/contact_us')
        self.config.add_route('login', '/login')

    def test_create_profile_view_get(self):
        self.request.referrer = '/'
        view = CreateProfile(self.request)
        info = view.get()
        self.assertTrue('rendered_form' in info)

    def test_create_profile_view_get_on_post(self):
        self.request.referrer = '/'
        view = CreateProfile(self.request)
        info = view.post()
        self.assertEqual(info.status_code, 405)

    def test_create_profile_view_post_no_args(self):
        self.request.referrer = '/'
        self.request.method = 'POST'
        view = CreateProfile(self.request)
        info = view.post()
        self.assertTrue('rendered_form' in info)

    def test_create_profile_view_submit_empty_form(self):
        request = testing.DummyRequest(post={'submit': ''})
        request.user = None
        request.db_session = MockSession()
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
            ('__start__', u'captcha:mapping'),
            ('captcha', u'x5J780'),
            ('__end__', u'captcha:mapping'),
            ('submit', u'submit'),
        ])
        request = testing.DummyRequest(post=data)
        request.user = None
        request.db_session = MockSession()
        view = CreateProfile(request)
        info = view.post()
        self.assertTrue('form' not in info.keys())

    def test_edit_profile_view(self):
        self.config.add_route('edit_profile', '/edit_profile/{username}/')
        user = create_user('testuser')
        request = testing.DummyRequest(path="/edit_profile/testuser/")
        request.db_session = MockSession(store=[user])
        request.matchdict['username'] = 'testuser'
        request.user = user
        request.referer = '/'
        view = EditProfile(request, MAX_DOMAIN_ATTEMPTS)
        view.target_username = 'test'
        view.current_username = 'test'
        info = view.get()
        self.assertTrue('rendered_form' in info)
