from unittest import TestCase

from sixfeetup.bowab.tests.mocks import MockQuery
from sixfeetup.bowab.tests.mocks import MockSession
import colander
from testfixtures import ShouldRaise

from speak_friend.forms.profiles import UserName


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

    def test_no_defaults(self):
        result = UserName()(None, 'barf')
        self.assertTrue(result is None)

    def test_username_available(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['jdoe'])
        result = UserName(db_session=db_session)(None, 'jsmith')
        self.assertTrue(result is None)

    def test_username_taken(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['jsmith'])
        msg = "Username already exists."
        node = colander.SchemaNode(colander.String(), name=u'username')
        # This will fail if the exception is not raised
        with ShouldRaise(colander.Invalid(node, msg)):
            UserName(db_session=db_session)(node, 'jsmith')

    def test_username_should_exist(self):
        db_session = MockSession()
        db_session.query = FilterMockQuery(['jdoe'])
        msg = "Username does not exist."
        node = colander.SchemaNode(colander.String(), name=u'username')
        # This will fail if the exception is not raised
        with ShouldRaise(colander.Invalid(node, msg)):
            UserName(should_exist=True, db_session=db_session)(node, 'jsmith')
