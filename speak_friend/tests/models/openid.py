from unittest import TestCase
from mock import Mock, call
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
        session = Mock()
        server_url = "http://test.net"
        store = SFOpenIDStore(session)
        store.getAssociation(server_url)
        session.query.filter_by.assert_called_with(server_url=server_url)

    def test_returning_association(self):
        session = Mock()
        server_url = "http://test.net"
        assoc = Association(server_url, 'asdf', 'aflasdkf', 5555, 555, 'adsf')

        # This is really gross, all to get mocks working.
        first = Mock(return_value=assoc)
        middle = Mock(first=first)
        filter_by = Mock(return_value=middle)
        session.query.filter_by = filter_by

        store = SFOpenIDStore(session)
        returned = store.getAssociation(server_url)
        self.assertEqual(assoc, returned)
