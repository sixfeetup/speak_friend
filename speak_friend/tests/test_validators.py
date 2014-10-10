from unittest import TestCase

from sixfeetup.bowab.tests.mocks import MockQuery
from sixfeetup.bowab.tests.mocks import MockSession
import colander
from testfixtures import ShouldRaise

from speak_friend.forms.profiles import DomainName
from speak_friend.forms.profiles import UserEmail
from speak_friend.forms.profiles import UserName
from speak_friend.forms.profiles import FQDN


class FilterMockQuery(MockQuery):

    def filter(self, *args):
        """Check the username value and set the store based on that
        """
        if args and args[0].right.value in self._store:
            self._store = [args[0].right.value]
        else:
            self._store = []
        return self


class TestUserNameValidator(TestCase):

    def setUp(self):
        self.node = colander.SchemaNode(colander.String(), name=u'username')

    def test_no_defaults(self):
        result = UserName()(self.node, 'barf')
        self.assertTrue(result is None)

    def test_username_available(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['jdoe'])
        result = UserName(db_session=db_session)(self.node, 'jsmith')
        self.assertTrue(result is None)

    def test_username_taken(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['jsmith'])
        msg = "Username already exists."
        # This will fail if the exception is not raised
        with ShouldRaise(colander.Invalid(self.node, msg)):
            UserName(db_session=db_session)(self.node, 'jsmith')

    def test_username_should_exist(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['jdoe'])
        msg = "Username does not exist."
        # This will fail if the exception is not raised
        with ShouldRaise(colander.Invalid(self.node, msg)):
            UserName(
                should_exist=True, db_session=db_session)(self.node, 'jsmith')


class TestFQDNValidator(TestCase):

    def setUp(self):
        self.node = colander.SchemaNode(colander.String(), name=u'domain')

    def test_valid_domain(self):
        result = FQDN()(self.node, 'google.com')
        self.assertTrue(result is None)

    def test_trailing_dot(self):
        result = FQDN()(self.node, 'google.com.')
        self.assertTrue(result is None)

    def test_wildcard(self):
        domain = '*.google.com'
        result = FQDN()(self.node, domain)
        self.assertTrue(result is None)

    def test_wildcard_middle_segment(self):
        domain = 'foo.*.bar.com'
        msg = 'Wildcard only allowed in leading segment.'
        with ShouldRaise(colander.Invalid(self.node, msg)):
            FQDN()(self.node, domain)

    def test_wildcard_segment(self):
        domain = 'foo.*.bar.com'
        msg = 'Wildcard only allowed in leading segment.'
        with ShouldRaise(colander.Invalid(self.node, msg)):
            FQDN()(self.node, domain)

    def test_wildcard_leading(self):
        domain = 'foo*.bar.com'
        msg = 'Wildcard must be first character in segment.'
        with ShouldRaise(colander.Invalid(self.node, msg)):
            FQDN()(self.node, domain)

    def test_too_long(self):
        domain = 'rly' * 86 + '.com'
        msg = 'Domain name is too long.'
        with ShouldRaise(colander.Invalid(self.node, msg)):
            FQDN()(self.node, domain)

    def test_segment_too_long(self):
        domain = 'foo.' + 'rly' * 22 + '.bar.com'
        msg = 'Segment is too long: {}.'.format('rly' * 22)
        with ShouldRaise(colander.Invalid(self.node, msg)):
            FQDN()(self.node, domain)

    def test_leading_dashes(self):
        domain = 'foo.-bar.com'
        msg = 'Names cannot begin or end with "-".'
        with ShouldRaise(colander.Invalid(self.node, msg)):
            FQDN()(self.node, domain)

    def test_trailing_dashes(self):
        domain = 'foo.bar-.com'
        msg = 'Names cannot begin or end with "-".'
        with ShouldRaise(colander.Invalid(self.node, msg)):
            FQDN()(self.node, domain)

    def test_alphanum(self):
        domain = 'foo.ba?r.com'
        msg = 'Invalid segment: "ba?r".'
        with ShouldRaise(colander.Invalid(self.node, msg)):
            FQDN()(self.node, domain)


class TestUserEmailValidator(TestCase):

    def setUp(self):
        self.node = colander.SchemaNode(colander.String(), name=u'email')

    def test_no_defaults(self):
        result = UserEmail()(self.node, 'foo@example.com')
        self.assertTrue(result is None)

    def test_email_edit(self):
        self.node.current_value = 'buster@example.com'
        result = UserEmail(for_edit=True)(self.node, 'buster@example.com')
        self.assertTrue(result)

    def test_email_available(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['jdoe@example.com'])
        result = UserEmail(
            should_exist=False, db_session=db_session)(self.node, 'a@b.com')
        self.assertTrue(result is None)

    def test_email_taken(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['jsmith@example.com'])
        msg = "Email address taken"
        # This will fail if the exception is not raised
        with ShouldRaise(colander.Invalid(self.node, msg)):
            v = UserEmail(msg=msg, should_exist=False, db_session=db_session)
            v(self.node, 'jsmith@example.com')


class TestDomainNameValidator(TestCase):

    def setUp(self):
        self.node = colander.SchemaNode(colander.String(), name=u'domain')

    def test_no_defaults(self):
        result = DomainName()(self.node, 'google.com')
        self.assertTrue(result is None)

    def test_domain_edit(self):
        self.node.current_value = 'google.com'
        result = DomainName(for_edit=True)(self.node, 'google.com')
        self.assertTrue(result)

    def test_domain_available(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['yahoo.com'])
        result = DomainName(
            should_exist=False, db_session=db_session)(self.node, 'google.com')
        self.assertTrue(result is None)

    def test_domain_taken(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['google.com'])
        msg = "Domain taken"
        # This will fail if the exception is not raised
        with ShouldRaise(colander.Invalid(self.node, msg)):
            v = DomainName(msg=msg, should_exist=False, db_session=db_session)
            v(self.node, 'google.com')
