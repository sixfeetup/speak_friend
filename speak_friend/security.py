from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import Everyone
from pyramid.security import authenticated_userid

from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile


Viewers = 'speak_friend.viewers'
Admins = 'speak_friend.admins'

def groupfinder(userid, request):
    session = DBSession()
    query = session.query(UserProfile)
    user = query.get(userid)
    groups = []
    if user:
        groups.append(Viewers)
    else:
        return None
    if user.is_superuser:
        groups.append(Admins)
    return groups

# Since we are not using ZODB + traversal, we just use
# this as a placeholder to attach ACLs to
class RootFactory(object):
    __acl__ = [
        (Allow, Authenticated, 'view'),
        (Allow, Admins, ALL_PERMISSIONS),
    ]
    def __init__(self, request):
        self.request = request


class EditProfileFactory(object):
    __acl__ = [
        (Allow, Authenticated, 'view'),
        (Allow, Admins, ALL_PERMISSIONS),
    ]
    def __init__(self, request):
        self.request = request
        target_username = request.matchdict['username']
        current_username = authenticated_userid(request)
        if target_username == current_username:
            self.__acl__.append(
                (Allow, current_username, 'edit'),
            )


class ChangePasswordFactory(object):
    __acl__ = [
        (Allow, Authenticated, 'view'),
    ]

    def __init__(self, request):
        self.request = request
        target_username = request.matchdict['username']
        current_username = authenticated_userid(request)
        if target_username == current_username:
            self.__acl__.append(
                (Allow, current_username, 'edit'),
            )
