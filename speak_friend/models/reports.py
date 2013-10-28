from sixfeetup.bowab.db import Base
from sixfeetup.bowab.db import CIText
from sixfeetup.bowab.db import JSON

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UnicodeText
from sqlalchemy import event
from sqlalchemy import func
from sqlalchemy.orm import relationship

from speak_friend.events import ACTIVITIES


class Activity(Base):
    __tablename__ = 'activities'
    __table_args__ = (
        {'schema': 'reports'}
    )
    activity = Column(
        UnicodeText,
        primary_key=True,
    )

    def __init__(self, activity):
        self.activity = activity

    def __repr__(self):
        return u"<Activity(%s)>" % self.activity

def after_activity_create(target, connection, **kw):
    for aname in ACTIVITIES:
        connection.execute(target.insert(), activity=aname)

event.listen(Activity.__table__, "after_create", after_activity_create)


class UserActivity(Base):
    __tablename__ = 'user_activity'
    __table_args__ = (
        {'schema': 'reports'}
    )
    user_activity_id = Column(
        Integer,
        primary_key=True
    )
    username = Column(
        CIText,
        ForeignKey("profiles.user_profiles.username"),
        nullable=False,
        index=True,
    )
    user = relationship(
        "UserProfile",
        primaryjoin="UserActivity.username==UserProfile.username",
        backref='activities',
    )
    activity = Column(
        UnicodeText,
        ForeignKey("reports.activities.activity"),
        nullable=False,
        index=True
    )
    activity_ts = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        index=True,
    )
    actor_username = Column(
        CIText,
        ForeignKey("profiles.user_profiles.username")
    )
    actor = relationship(
        "UserProfile",
        primaryjoin="UserActivity.username==UserProfile.username",
    )
    came_from = Column(
        UnicodeText,
    )
    came_from_fqdn = Column(
        UnicodeText,
        index=True,
    )
    activity_detail = Column(
        JSON,
    )

    def __init__(self, **attrs):
        if 'username' not in attrs and \
           'user' not in attrs:
            raise KeyError('Missing key: user')
        elif 'user' in attrs and \
           'username' not in attrs:
            attrs['username'] = attrs['user'].username
        if 'actor' in attrs and \
           attrs['actor'] and \
           'actor_username' not in attrs:
            attrs['actor_username'] = attrs['actor'].username
        if 'activity' not in attrs:
            raise KeyError('Missing key: activity')

        for attr, value in attrs.items():
            if attr in self.__table__.columns:
                setattr(self, attr, value)

    def __repr__(self):
        return u"<UserActivity(%s, %s, %s)>" % (self.username, self.activity,
                                                self.activity_ts)

    @classmethod
    def last_user_activity(cls, session, user,
                           *activities,
                           **extra_filters):
        qry = session.query(UserActivity)
        qry = qry.filter(UserActivity.user == user,
                         UserActivity.activity.in_(activities))
        qry = qry.filter_by(**extra_filters)
        qry = qry.order_by(UserActivity.activity_ts.desc())
        return qry.first()

    @classmethod
    def last_checkid(cls, session, user):
        return cls.last_user_activity(session, user,
                                      u'authorize_checkid', u'login')
