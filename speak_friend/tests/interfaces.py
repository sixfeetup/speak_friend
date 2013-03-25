from unittest import TestCase

from mock import Mock
from pyramid import testing

from zope.interface import Interface
from zope.interface import implementer

from speak_friend.tests.mocks import create_user


class ITestInterface(Interface):
    pass


@implementer(ITestInterface)
class TestInterface(object):
    pass


class BaseInterface(TestCase):
    def _getTargetInterface(self):
        return ITestInterface

    def _getTargetClass(self):
        return TestInterface

    def _makeOne(self, *arg, **kw):
        cls = self._getTargetClass()
        return cls(*arg, **kw)

    def test_implements(self):
        from pyramid.interfaces import IResponse
        cls = self._getTargetClass()
        iface = self._getTargetInterface()
        self.assertTrue(iface.implementedBy(cls))

    def test_provides(self, *arg, **kw):
        inst = self._makeOne(*arg, **kw)
        iface = self._getTargetInterface()
        self.assertTrue(iface.providedBy(inst))


class TestOpenIDStore(BaseInterface):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IOpenIDStore
        return IOpenIDStore

    def _getTargetClass(self):
        from speak_friend.models.open_id import SFOpenIDStore
        return SFOpenIDStore

    def test_provides(self, *arg, **kw):
        super(TestOpenIDStore, self).test_provides(Mock())


class TestUserActivity(BaseInterface):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IUserActivity
        return IUserActivity

    def _getTargetClass(self):
        from speak_friend.events import UserActivity
        return UserActivity

    def test_provides(self, **activity_detail):
        from speak_friend.events import ACTIVITIES
        if None not in ACTIVITIES:
            ACTIVITIES.append(None)
        req = testing.DummyRequest(referrer='http://foo.com')
        req['REMOTE_ADDR'] = '192.168.1.1'
        user = create_user('sfupadmin')
        req.user = user
        super(TestUserActivity, self).test_provides(req, user,
                                                    **activity_detail)


class TestAccountCreated(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IAccountCreated
        return IAccountCreated

    def _getTargetClass(self):
        from speak_friend.events import AccountCreated
        return AccountCreated


class TestAccountDisabled(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IAccountDisabled
        return IAccountDisabled

    def _getTargetClass(self):
        from speak_friend.events import AccountDisabled
        return AccountDisabled


class TestAccountEnabled(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IAccountEnabled
        return IAccountEnabled

    def _getTargetClass(self):
        from speak_friend.events import AccountEnabled
        return AccountEnabled


class TestAccountLocked(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IAccountLocked
        return IAccountLocked

    def _getTargetClass(self):
        from speak_friend.events import AccountLocked
        return AccountLocked


class TestAccountUnlocked(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IAccountUnlocked
        return IAccountUnlocked

    def _getTargetClass(self):
        from speak_friend.events import AccountUnlocked
        return AccountUnlocked


class TestLoggedIn(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import ILoggedIn
        return ILoggedIn

    def _getTargetClass(self):
        from speak_friend.events import LoggedIn
        return LoggedIn


class TestLoginFailed(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import ILoginFailed
        return ILoginFailed

    def _getTargetClass(self):
        from speak_friend.events import LoginFailed
        return LoginFailed


class TestLoggedOut(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import ILoggedOut
        return ILoggedOut

    def _getTargetClass(self):
        from speak_friend.events import LoggedOut
        return LoggedOut


class TestPasswordChanged(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IPasswordChanged
        return IPasswordChanged

    def _getTargetClass(self):
        from speak_friend.events import PasswordChanged
        return PasswordChanged


class TestProfileChanged(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IProfileChanged
        return IProfileChanged

    def _getTargetClass(self):
        from speak_friend.events import ProfileChanged
        return ProfileChanged


class TestPasswordRequested(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IPasswordRequested
        return IPasswordRequested

    def _getTargetClass(self):
        from speak_friend.events import PasswordRequested
        return PasswordRequested


class TestPasswordReset(TestUserActivity):
    def _getTargetInterface(self):
        from speak_friend.interfaces import IPasswordReset
        return IPasswordReset

    def _getTargetClass(self):
        from speak_friend.events import PasswordReset
        return PasswordReset
