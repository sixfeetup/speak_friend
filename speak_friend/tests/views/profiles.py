from passlib.apps import ldap_context

from pyramid import testing
from webob.multidict import MultiDict
from speak_friend.views.accounts import CreateProfile, EditProfile, LoginView

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
        # The next 4 lines silence silly SA optimization warnings
        import warnings
        from sqlalchemy import exc as sa_exc
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)

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
        request.referrer = '/'
        view = EditProfile(request, MAX_DOMAIN_ATTEMPTS)
        view.target_username = 'test'
        view.current_username = 'test'
        info = view.get()
        self.assertTrue('rendered_form' in info)

    def test_login_view(self):
        """
        Test the user login view.
        """
        request = self.request

        request.referrer = '/'
        request.path = request.path_info = "/login/"
        self.config.add_route('login', '/login/')
        request.matched_route = self.config.get_routes_mapper(
            ).get_route('login')

        self.config.registry.password_context = ldap_context
        user = create_user('testuser')
        secret = 'secret'
        encrypted = self.config.registry.password_context.encrypt(secret)
        user.password_hash = encrypted
        request.user = user

        request.session.save = lambda: None
        request.environ['REMOTE_ADDR'] = '127.0.0.2'
        request.db_session = MockSession(store=[user])
        request.matchdict['username'] = 'testuser'
        view = LoginView(request, MAX_DOMAIN_ATTEMPTS)
        view.target_username = 'test'
        view.current_username = 'test'

        info = view.get()
        self.assertTrue('rendered_form' in info)

        view.request.POST.update(
            submit='1',
            came_from=request.referrer,
            csrf_token=request.session.get_csrf_token(),
            login=user.username, password=secret)
        post = view.post()
        self.assertIn(
            'Location', post.headers, 'Missing redirect location')
        self.assertEqual(
            post.headers['Location'], '/', 'Wrong redirect location')
