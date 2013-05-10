import datetime
import time

from unittest import TestCase
from mock import Mock, call

from sixfeetup.bowab.tests.mocks import MockQuery

from speak_friend.models.open_id import SFOpenIDStore, Association, Nonce



__all__ = [ 'OpenIDStoreTest', 'AssociationTests' ]


def mock_filter(**kwargs):
    if 'server_url' in kwargs:
        assocs = [assoc for assoc in self.store
                  if assoc.server_url == kwargs['server_url']]
        if len(assocs) == 1:
            return assocs[0]


class OpenIDStoreTest(TestCase):
    def test_method_presence(self):
        store = SFOpenIDStore(Mock())
        self.assertTrue(hasattr(store, 'storeAssociation'))
        self.assertTrue(hasattr(store, 'getAssociation'))
        self.assertTrue(hasattr(store, 'removeAssociation'))
        self.assertTrue(hasattr(store, 'useNonce'))

    def test_creation(self):
        session = Mock()
        session.sentinel = "here"
        store = SFOpenIDStore(session)
        self.assertEqual(store.session.sentinel, "here")

    def test_storing_association(self):
        session = Mock()
        server_url = "http://test.net"
        raw_assoc = Mock()
        store = SFOpenIDStore(session)
        assoc = store.storeAssociation(server_url, raw_assoc)
        self.assertEqual(session.add.call_count, 1)
        self.assertEqual(session.add.call_args, call(assoc))

    def test_filtering_association(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association("http://test.com", 'asdf', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')
        assoc2 = Association(server_url, 'asdf', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')

        session = Mock()
        session.query = MockQuery(store=[assoc1, assoc2])

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url)
        for attr in ('handle', 'secret',
                     'issued', 'lifetime', 'assoc_type'):
            self.assertEqual(getattr(returned, attr),
                             getattr(assoc2, attr))

    def test_returning_association(self):
        session = Mock()
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc = Association(server_url, 'asdf', 'aflasdkf', issued, lifetime, 'HMAC-SHA1')
        session.query = MockQuery(store=[assoc])

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url)
        for attr in ('handle', 'secret',
                     'issued', 'lifetime', 'assoc_type'):
            self.assertEqual(getattr(returned, attr),
                             getattr(assoc, attr))

    def test_failed_assoc_lookup(self):
        session = Mock()
        session.query = MockQuery()
        server_url = "http://test.net"

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url)
        self.assertTrue(returned is None)

    def test_assoc_lookup_by_handle(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association(server_url, 'asdf', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')
        assoc2 = Association(server_url, 'asdf1', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')

        session = Mock()
        session.query = MockQuery(store=[assoc1, assoc2])

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url, handle='asdf1')
        for attr in ('handle', 'secret',
                     'issued', 'lifetime', 'assoc_type'):
            self.assertEqual(getattr(returned, attr),
                             getattr(assoc2, attr))

    def test_assoc_lookup_by_handle_server_url(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association("http://test.com", 'asdf', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')
        assoc2 = Association(server_url, 'asdf1', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')

        session = Mock()
        session.query = MockQuery(store=[assoc1, assoc2])

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url, handle='asdf1')
        for attr in ('handle', 'secret',
                     'issued', 'lifetime', 'assoc_type'):
            self.assertEqual(getattr(returned, attr),
                             getattr(assoc2, attr))

    def test_expired_assoc_cleanup(self):
        server_url = "http://test.net"
        day = 60 * 60 * 24
        issued = time.mktime(datetime.datetime(2010, 1, 20).timetuple())
        storage = []
        for i in xrange(0, 10):
            lifetime = day + i
            new_assoc = Association(server_url, 'asdf', 'afla', issued,
                                    lifetime, 'HMAC-SHA1')
            storage.append(new_assoc)

        session = Mock()
        session.query = MockQuery(store=storage)

        store = SFOpenIDStore(session)
        store.cleanupAssociations()
        self.assertEqual(session.query._store, [])

    def test_remove_association_success(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association("http://test.com", 'asdf', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')
        assoc2 = Association(server_url, 'asdf', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')

        session = Mock()
        session.query = MockQuery(store=[assoc1, assoc2])

        store = SFOpenIDStore(session)
        returned = store.removeAssociation(server_url, handle='asdf')
        self.assertEqual(returned, True)

    def test_remove_association_fail_handle(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association("http://test.net", 'asdf', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')

        session = Mock()
        session.query = MockQuery(store=[assoc1])

        store = SFOpenIDStore(session)
        returned = store.removeAssociation(server_url, handle='asdf1')
        self.assertEqual(returned, False)

    def test_remove_association_fail_url(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association("http://test.com", 'asdf', 'aflasdkf',
                             issued, lifetime, 'HMAC-SHA1')

        session = Mock()
        session.query = MockQuery(store=[assoc1])

        store = SFOpenIDStore(session)
        returned = store.removeAssociation(server_url, handle='asdf')
        self.assertEqual(returned, False)

    def test_use_nonce_success(self):
        server_url = "http://test.net"
        timestamp = int(time.time())
        salt = "asdfgadfgj"

        session = Mock()
        session.query = MockQuery()

        store = SFOpenIDStore(session)
        use_nonce = store.useNonce(server_url, timestamp, salt)
        self.assertEqual(use_nonce, True)

    def test_use_nonce_fail(self):
        server_url = "http://test.net"
        timestamp = int(time.time())
        salt = "asdfgadfgj"

        nonce = Nonce(server_url, timestamp, salt)

        session = Mock()
        session.query = MockQuery(store=[nonce])

        store = SFOpenIDStore(session)
        use_nonce = store.useNonce(server_url, timestamp, salt)
        self.assertEqual(use_nonce, False)

    def test_use_nonce_out_of_skew_pass(self):
        from openid.store.nonce import SKEW
        server_url = "http://test.net"
        timestamp = int(time.time())
        salt = "asdfgadfgj"

        nonce = Nonce(server_url, timestamp + SKEW + 5, salt)

        session = Mock()
        session.query = MockQuery(store=[nonce])

        def fake_filter(*args):
            return MockQuery(store=[])

        session.query.filter = fake_filter

        store = SFOpenIDStore(session)
        use_nonce = store.useNonce(server_url, timestamp, salt)
        self.assertEqual(use_nonce, True)



class AssociationTests(TestCase):

    def test_is_expired_true(self):
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime(2010, 1, 20).timetuple())
        assoc = Association('http://test.net', 'asdf', 'asdf',
                            issued, lifetime, 'HMAC-SHA1')
        expired = assoc.is_expired()
        self.assertTrue(expired)

    def test_is_expired_false(self):
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc = Association('http://test.net', 'asdf', 'asdf',
                            issued, lifetime, 'HMAC-SHA1')
        expired = assoc.is_expired()
        self.assertFalse(expired)
