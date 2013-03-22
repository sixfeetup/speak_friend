from zope.interface import implementer
from zope.interface import Interface

from speak_friend.interfaces import IUserActivity
from speak_friend.interfaces import IAccountCreated
from speak_friend.interfaces import IAccountDisabled
from speak_friend.interfaces import IAccountEnabled
from speak_friend.interfaces import IAccountLocked
from speak_friend.interfaces import IAccountUnlocked
from speak_friend.interfaces import ILoggedIn
from speak_friend.interfaces import ILoginFailed
from speak_friend.interfaces import ILoggedOut
from speak_friend.interfaces import IPasswordChanged
from speak_friend.interfaces import IPasswordRequested
from speak_friend.interfaces import IProfileChanged

ACTIVITIES = [
    u'change_password',
    u'create_account',
    u'disable_account',
    u'enable_account',
    u'lock_account',
    u'login',
    u'fail_login',
    u'logout',
    u'unlock_account',
    u'change_profile',
    u'request_password',
]


@implementer(IUserActivity)
class UserActivity(object):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user takes an action using :app:`speak_friend`.
    The event instance has an attribute, ``request``, which is a
    :term:`request` object.  This event class implements the
    :class:`speak_friend.interfaces.IUserActivity` interface.
    The list of activities can be found in:
    ``speak_friend.events.ACTIVITIES``."""
    def __init__(self, request, user, activity,
                 actor=None, **activity_detail):
        if activity not in ACTIVITIES:
            raise ValueError(u'No such activity defined: %s' % activity)
        self.request = request
        self.user = user
        self.activity = activity
        self.actor = actor
        self.activity_detail = activity_detail


@implementer(IAccountCreated)
class AccountCreated(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is created. See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(AccountCreated, self).__init__(request, user,
              u'create_account', actor, **activity_detail)


@implementer(IAccountDisabled)
class AccountDisabled(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is disabled by an admin.
    See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(AccountDisabled, self).__init__(request, user,
              u'disable_account', actor, **activity_detail)


@implementer(IAccountEnabled)
class AccountEnabled(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is enabled by an admin.
    See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(AccountEnabled, self).__init__(request, user,
              u'enable_account', actor, **activity_detail)


@implementer(IAccountLocked)
class AccountLocked(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is locked. See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(AccountLocked, self).__init__(request, user,
              u'lock_account', actor, **activity_detail)


@implementer(IAccountUnlocked)
class AccountUnlocked(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is unlocked. See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(AccountUnlocked, self).__init__(request, user,
              u'unlock_account', actor, **activity_detail)


@implementer(ILoggedIn)
class LoggedIn(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user logs in. See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        if u'ip_address' not in activity_detail:
            activity_detail[u'ip_address'] = request['REMOTE_ADDR']
        super(LoggedIn, self).__init__(request, user,
              u'login', actor, **activity_detail)


@implementer(ILoggedOut)
class LoggedOut(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user logs out. See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(LoggedOut, self).__init__(request, user,
              u'logout', actor, **activity_detail)


@implementer(ILoginFailed)
class LoginFailed(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user fails to log in. See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(LoginFailed, self).__init__(request, user,
              u'fail_login', actor, **activity_detail)


@implementer(IPasswordChanged)
class PasswordChanged(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user changes their password. See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(PasswordChanged, self).__init__(request, user,
              u'change_password', actor, **activity_detail)


@implementer(IProfileChanged)
class ProfileChanged(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user changes their profile (but not their password).
    See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(ProfileChanged, self).__init__(request, user,
              u'change_profile', actor, **activity_detail)


@implementer(IPasswordRequested)
class PasswordRequested(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user requests their password to be reset.
    See :class:`UserActivity`.
    """
    def __init__(self, request, user,
                 actor=None, **activity_detail):
        super(PasswordRequested, self).__init__(request, user,
              u'request_password', actor, **activity_detail)
