import datetime
import time

from unittest import TestCase
from mock import Mock, call

from speak_friend.tests.mocks import MockQuery
from speak_friend.models.openid import SFOpenIDStore, Association, Nonce


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
        assoc = Mock()
        store = SFOpenIDStore(session)
        store.storeAssociation(server_url, assoc)
        self.assertEqual(session.commit.call_count, 1)
        self.assertEqual(session.add.call_args, call(assoc))

    def test_filtering_association(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association("http://test.com", 'asdf', 'aflasdkf',
                             issued, lifetime, 'adsf')
        assoc2 = Association(server_url, 'asdf', 'aflasdkf',
                             issued, lifetime, 'adsf')

        session = Mock()
        session.query = MockQuery(store=[assoc1, assoc2])

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url)
        self.assertEqual(returned, assoc2)

    def test_returning_association(self):
        session = Mock()
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc = Association(server_url, 'asdf', 'aflasdkf', issued, lifetime, 'adsf')
        session.query = MockQuery(store=[assoc])

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url)
        self.assertEqual(assoc, returned)

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
                             issued, lifetime, 'adsf')
        assoc2 = Association(server_url, 'asdf1', 'aflasdkf',
                             issued, lifetime, 'adsf')

        session = Mock()
        session.query = MockQuery(store=[assoc1, assoc2])

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url, handle='asdf1')
        self.assertEqual(returned, assoc2)

    def test_assoc_lookup_by_handle_server_url(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association("http://test.com", 'asdf', 'aflasdkf',
                             issued, lifetime, 'adsf')
        assoc2 = Association(server_url, 'asdf1', 'aflasdkf',
                             issued, lifetime, 'adsf')

        session = Mock()
        session.query = MockQuery(store=[assoc1, assoc2])

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url, handle='asdf1')
        self.assertEqual(returned, assoc2)

    def test_expired_assoc_cleanup(self):
        server_url = "http://test.net"
        day = 60 * 60 * 24
        issued = time.mktime(datetime.datetime(2010, 1, 20).timetuple())
        storage = []
        for i in xrange(0, 10):
            lifetime = day + i
            new_assoc = Association(server_url, 'asdf', 'afla', issued,
                                    lifetime, 'adsf')
            storage.append(new_assoc)

        session = Mock()
        session.query = MockQuery(store=storage)

        store = SFOpenIDStore(session)
        store.cleanExpiredAssociations()
        self.assertEqual(session.query._store, [])

    def test_remove_association_success(self):
        server_url = "http://test.net"
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc1 = Association("http://test.com", 'asdf', 'aflasdkf',
                             issued, lifetime, 'adsf')
        assoc2 = Association(server_url, 'asdf', 'aflasdkf',
                             issued, lifetime, 'adsf')

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
                             issued, lifetime, 'adsf')

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
                             issued, lifetime, 'adsf')

        session = Mock()
        session.query = MockQuery(store=[assoc1])

        store = SFOpenIDStore(session)
        returned = store.removeAssociation(server_url, handle='asdf')
        self.assertEqual(returned, False)





class AssociationTests(TestCase):

    def test_is_expired_true(self):
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime(2010, 1, 20).timetuple())
        assoc = Association('http://test.net', 'asdf', 'asdf',
                            issued, lifetime, 'asdf')
        expired = assoc.is_expired()
        self.assertTrue(expired)

    def test_is_expired_false(self):
        lifetime = 60 * 60 * 24 * 5 # 5 days in seconds
        issued = time.mktime(datetime.datetime.now().timetuple())
        assoc = Association('http://test.net', 'asdf', 'asdf',
                            issued, lifetime, 'asdf')
        expired = assoc.is_expired()
        self.assertFalse(expired)
