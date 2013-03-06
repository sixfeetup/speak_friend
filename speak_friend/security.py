from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile


def userfinder(userid, request):
    session = DBSession()
    query = session.query(UserProfile)
    query = query.filter(UserProfile.username == userid)
    user = query.first()
    if user:
        return user.username
    else:
        return None
