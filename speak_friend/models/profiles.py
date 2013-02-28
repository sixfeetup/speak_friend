import uuid

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import SmallInteger
from sqlalchemy import UnicodeText
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from speak_friend.models import Base


class DomainProfile(Base):
    __tablename__ = 'domain_profiles'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    name = Column(UnicodeText, primary_key=True)
    password_valid = Column(Integer) # minutes
    max_attempts = Column(SmallInteger)

    def __init__(self, name, password_valid, max_attempts):
        self.name = name
        self.password_valid = password_valid
        self.max_attempts = max_attempts

    def __repr__(self):
        return u'<DomainProfile(%s)>' % self.name

    def password_always_required(self):
        """if password is valid for 0 minutes, it is always required
        """
        return not bool(self.password_valid)


class UserProfile(Base):
    __tablename__ = 'user_profiles'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    username = Column(UnicodeText, primary_key=True)
    first_name = Column(UnicodeText)
    last_name = Column(UnicodeText)
    email = Column(UnicodeText, nullable=False)
    password_hash = Column(UnicodeText)
    password_salt = Column(UnicodeText)
    login_attempts = Column(Integer)
    admin_disabled = Column(Boolean, default=False)


    def __init__(self, username, first_name, last_name, email,
                 password_hash, password_salt, login_attempts, admin_disabled):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = password_hash
        self.password_salt = password_salt
        self.login_attempts = login_attempts
        self.admin_disabled = admin_disabled

    def __repr__(self):
        return u"<UserProfile(%s)>" % self.username


class ResetToken(Base):
    __tablename__ = 'reset_tokens'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    username = Column(
        UnicodeText,
        ForeignKey(UserProfile.username),
        primary_key=True,
    )
    user = relationship(
        UserProfile,
        foreign_keys=[UserProfile.username],
        primaryjoin='ResetToken.username==UserProfile.username',
    )
    token = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
    )
    came_from = Column(UnicodeText)
    generation_ts = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        index=True,
    )


    def __init__(self, username, token=None, came_from=None):
        self.username = username
        if token is None:
            token = uuid.uuid4()
        self.token = token
        self.came_from = came_from

    def __repr__(self):
        return u"<ResetToken(%s)>" % self.token
