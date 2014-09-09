from sixfeetup.bowab.tests import mocks

from speak_friend.tests.common import SFBaseCase


class MockSession(mocks.MockSession):
    """
    Differentiate between DomainProfiles and UserActivities.
    """

    def __init__(self, store=None):
        super(MockSession, self).__init__(store=store)
        self.query = MockQuery(store=self._store)


class MockQuery(mocks.MockQuery):
    """
    Differentiate between DomainProfiles and UserActivities.
    """

    def __call__(self, model):
        """
        Differentiate between DomainProfiles and UserActivities.
        """
        if model.__name__ == 'UserActivity':
            return mocks.MockQuery(self._store[:1])(model)
        return mocks.MockQuery(self._store[1:])


class SFTemplateAPITests(SFBaseCase):
    def setUp(self):
        super(SFTemplateAPITests, self).setUp()
        self.request.referrer = ''
        self.request.POST = {}

        from speak_friend.api import SFTemplateAPI
        self.api = SFTemplateAPI(self.request, self.request.GET)

    def test_settings(self):
        self.assertTrue(hasattr(self.api, 'settings'))

    def test_macros(self):
        self.assertTrue(hasattr(self.api, 'macros'))

    def test_resources(self):
        self.assertTrue(hasattr(self.api, 'css_resources'))
        self.assertTrue(hasattr(self.api, 'js_resources'))

    def test_current_year(self):
        self.assertTrue(hasattr(self.api, 'utc_now'))

    def test_default_domain(self):
        """
        No API domain without a referrer or came_from.
        """
        self.request.user = None
        self.request.referrer = None
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNone(
            self.api.last_checkid_domain, 'Wrong default API domain')

    def test_referrer_non_existent_domain(self):
        """
        No API domain for HTTP referrers for non-existent domain objects.
        """
        self.request.user = None
        self.request.referrer = 'http://foo.com/'
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNone(
            self.api.last_checkid_domain, 'Wrong domain from referrer')

    def test_referrer_existing_domain(self):
        """
        API domain for HTTP referrers for existing domain objects.
        """
        from speak_friend.models import profiles
        self.request.user = None
        foo_domain = profiles.DomainProfile(name='foo.com', password_valid=-1)
        self.request.db_session = mocks.MockSession([foo_domain])
        self.request.referrer = 'http://{0}/'.format(foo_domain.name)
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNotNone(
            self.api.last_checkid_domain,
            'Missing domain from referrer for existing domain')
        self.assertEqual(
            self.api.last_checkid_domain.name, foo_domain.name,
            'Wrong domain from referrer for existing domain')

    def test_get_came_from_non_existent_domain(self):
        """
        No API domain for came_from GET query param for non-existent domains.
        """
        self.request.user = None
        self.request.GET['came_from'] = 'http://foo.com/'
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNone(
            self.api.last_checkid_domain, 'Wrong domain from came_from')

    def test_get_came_from_existing_domain(self):
        """
        API domain for came_from GET query param for existing domain objects.
        """
        from speak_friend.models import profiles
        self.request.user = None
        foo_domain = profiles.DomainProfile(name='foo.com', password_valid=-1)
        self.request.db_session = mocks.MockSession([foo_domain])
        self.request.GET['came_from'] = 'http://{0}/'.format(foo_domain.name)
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNotNone(
            self.api.last_checkid_domain,
            'Missing domain from came_from for existing domain')
        self.assertEqual(
            self.api.last_checkid_domain.name, foo_domain.name,
            'Wrong domain from came_from for existing domain')

    def test_post_came_from_non_existent_domain(self):
        """
        No API domain for came_from POST query param for non-existent domains.
        """
        self.request.user = None
        self.request.POST['came_from'] = 'http://foo.com/'
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNone(
            self.api.last_checkid_domain, 'Wrong domain from came_from')

    def test_post_came_from_existing_domain(self):
        """
        API domain for came_from POST query param for existing domain objects.
        """
        from speak_friend.models import profiles
        self.request.user = None
        foo_domain = profiles.DomainProfile(name='foo.com', password_valid=-1)
        self.request.db_session = mocks.MockSession([foo_domain])
        self.request.POST['came_from'] = 'http://{0}/'.format(foo_domain.name)
        self.api.rendering_val = self.request.POST
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNotNone(
            self.api.last_checkid_domain,
            'Missing domain from came_from for existing domain')
        self.assertEqual(
            self.api.last_checkid_domain.name, foo_domain.name,
            'Wrong domain from came_from for existing domain')

    def test_session_non_existent_domain(self):
        """
        No API domain for Beaker sessions for non-existent domain objects.
        """
        from speak_friend.models import reports
        foo_activity = reports.UserActivity(
            user=self.request.user, activity='authorize_checkid',
            came_from='http://foo.com', came_from_fqdn='foo.com')
        self.request.db_session = MockSession([foo_activity])
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNone(
            self.api.last_checkid_domain, 'Wrong domain from session')

    def test_session_existing_domain(self):
        """
        API domain for Beaker sessions for existing domain objects.
        """
        from speak_friend.models import profiles
        from speak_friend.models import reports
        foo_domain = profiles.DomainProfile(name='foo.com', password_valid=-1)
        foo_activity = reports.UserActivity(
            user=self.request.user, activity='authorize_checkid',
            came_from='http://foo.com', came_from_fqdn='foo.com')
        self.request.db_session = MockSession([foo_activity, foo_domain])
        self.assertTrue(
            hasattr(self.api, 'last_checkid_domain'),
            'Missing API domain attribute')
        self.assertIsNotNone(
            self.api.last_checkid_domain,
            'Missing domain from session for existing domain')
        self.assertEqual(
            self.api.last_checkid_domain.name, foo_domain.name,
            'Wrong domain from session for existing domain')
