from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import SmallInteger
from sqlalchemy import UnicodeText

from speak_friend.models import Base


class Domain(Base):
    __tablename__ = 'domain_profiles'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(UnicodeText, unique=True)
    password_valid = Column(Integer) # minutes
    max_attempts = Column(SmallInteger)

    def __init__(self, id, name, password_valid, max_attempts):
        self.id = id
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
    email = Column(UnicodeText)
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
