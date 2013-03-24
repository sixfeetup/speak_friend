from unittest import TestCase

from pyramid import testing

from speak_friend.tests.mocks import MockPasswordValidator
from speak_friend.tests.mocks import MockSession
from speak_friend.tests.mocks import create_user


class SFBaseCase(TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.add_settings({
            'recaptcha_private_key': 'foo',
            'recaptcha_options': '',
            'recaptcha_public_key': 'bar',
            'site_name': "Test",
        })
        self.config.add_route('yadis', '/yadis.xml')
        #self.config.add_request_method(get_user, 'user', reify=True)
        self.request = testing.DummyRequest()
        self.request.user = create_user('sfupadmin')
        self.request.db_session = MockSession()
        self.request.registry.password_validator = MockPasswordValidator()

    def tearDown(self):
        testing.tearDown()


def get_user(request):
    return create_user('sfupadmin')
