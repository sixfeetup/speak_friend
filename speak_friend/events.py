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
    def __init__(self, request, username, activity,
                 actor_username=None, activity_detail=None):
        if activity not in ACTIVITIES:
            raise ValueError(u'No such activity defined: %s' % activity)
        self.request = request
        self.username = username
        self.activity = activity
        self.actor_username = actor_username
        self.activity_detail = activity_detail


@implementer(IAccountCreated)
class AccountCreated(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is created. See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(AccountCreated, self, request, username,
              'create_account', actor_username, activity_detail)


@implementer(IAccountDisabled)
class AccountDisabled(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is disabled by an admin.
    See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(AccountDisabled, self, request, username,
              'disable_account', actor_username, activity_detail)


@implementer(IAccountEnabled)
class AccountEnabled(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is enabled by an admin.
    See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(AccountEnabled, self, request, username,
              'enable_account', actor_username, activity_detail)


@implementer(IAccountLocked)
class AccountLocked(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is locked. See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(AccountLocked, self, request, username,
              'lock_account', actor_username, activity_detail)


@implementer(IAccountUnlocked)
class AccountUnlocked(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user's account is unlocked. See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(AccountUnlocked, self, request, username,
              'unlock_account', actor_username, activity_detail)


@implementer(ILoggedIn)
class LoggedIn(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user logs in. See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(LoggedIn, self, request, username,
              'login', actor_username, activity_detail)


@implementer(ILoginFailed)
class LoginFailed(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user fails to log in. See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(LoginFailed, self, request, username,
              'fail_login', actor_username, activity_detail)


@implementer(ILoggedOut)
class LoggedOut(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user logs out. See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(LoggedOut, self, request, username,
              'logout', actor_username, activity_detail)


@implementer(IPasswordChanged)
class PasswordChanged(UserActivity):
    """ An instance of this class is emitted as an :term:`event`
    whenever a user changes their password. See :class:`UserActivity`.
    """
    def __init__(self, request, username,
                 actor_username=None, activity_detail=None):
        super(PasswordChanged, self, request, username,
              'change_password', actor_username, activity_detail)
