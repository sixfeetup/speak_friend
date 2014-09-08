from speak_friend.tests.common import SFBaseCase
from speak_friend.views.open_id import OpenIDProvider


class OpenIdViewTests(SFBaseCase):

    def setUp(self):
        super(OpenIdViewTests, self).setUp()
        self.config.add_route('home', '/')
        self.config.add_route('openid_provider', '/openid_provider')

    def test_openid_process_empty(self):
        provider = OpenIDProvider(self.request)
        result = provider.process({})
        self.assertEqual(result, '')

    def test_openid_process_malformed(self):
        provider = OpenIDProvider(self.request)
        result = provider.process({
            'openid.mode': 'checkid_setup',
            'openid.identity': 'http://example.com/jsmith',
            'openid.claimed_id': 'http://example.com/jsmith',
            'openid.return_to': '//google.com/foo',
        })
        self.assertEqual(result, '')

    def test_openid_process_bad_mode(self):
        provider = OpenIDProvider(self.request)
        result = provider.process({
            'openid.mode': 'not_real_mode',
            'openid.identity': 'http://example.com/jsmith',
            'openid.claimed_id': 'http://example.com/jsmith',
            'openid.return_to': 'http://google.com',
        })
        self.assertEqual(result, '')
