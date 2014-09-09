from pyramid import testing

from speak_friend.tests.common import SFBaseCase
from speak_friend.utils import get_domain
from speak_friend.utils import get_referrer


class UtilsTests(SFBaseCase):
    def test_get_referrer(self):
        req = testing.DummyRequest(referrer='http://foo.com')
        referrer = get_referrer(req)
        self.assertTrue(referrer == 'http://foo.com')

    def test_get_no_referrer(self):
        req = testing.DummyRequest(referrer='')
        referrer = get_referrer(req)
        self.assertTrue(referrer == '/')

    def test_get_domain(self):
        req = testing.DummyRequest(referrer='http://foo.com')
        domain = get_domain(req)
        self.assertTrue(domain == 'foo.com')

    def test_get_string_domain(self):
        domain = get_domain('http://foo.com')
        self.assertTrue(domain == 'foo.com')

    def test_get_no_domain(self):
        domain = get_domain('')
        self.assertTrue(domain == '')

    def test_get_domain_with_port(self):
        domain = get_domain('http://foo.com:123')
        self.assertTrue(domain == 'foo.com')
