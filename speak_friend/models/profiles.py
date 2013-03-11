import uuid

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import FetchedValue
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import SmallInteger
from sqlalchemy import UnicodeText
from sqlalchemy import event
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from speak_friend.models import Base
from speak_friend.forms.controlpanel import domain_defaults_schema


class DomainProfile(Base):
    __tablename__ = 'domain_profiles'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    name = Column(UnicodeText, primary_key=True)
    password_valid = Column(Integer, default=-1) # minutes
    max_attempts = Column(SmallInteger, default=-1)

    def __init__(self, name, password_valid, max_attempts):
        self.name = name
        self.password_valid = password_valid
        self.max_attempts = max_attempts

    def __repr__(self):
        return u'<DomainProfile(%s)>' % self.name

    def get_password_valid(self, cp):
        """return value of password_valid, or control panel default if < 0
        """
        pw_valid = self.password_valid
        if pw_valid < 0:
            current = cp.saved_sections.get(domain_defaults_schema.name)
            if current and current.panel_values:
                pw_valid = current.panel_values['password_valid']
            else:
                for child in domain_defaults_schema.children:
                    if child.name == 'password_valid':
                        pw_valid = child.default
        return pw_valid

    def get_max_attempts(self, cp):
        """return value of max_attempts, or control panel default if < 0
        """
        max_attempts = self.max_attempts
        if max_attempts < 0:
            current = cp.saved_sections.get(domain_defaults_schema.name)
            if current and current.panel_values:
                max_attempts = current.panel_values['max_attempts']
            else:
                for child in domain_defaults_schema.children:
                    if child.name == 'max_attempts':
                        max_attempts = child.default
        return max_attempts


class UserProfile(Base):
    __tablename__ = 'user_profiles'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    username = Column(UnicodeText, primary_key=True)
    first_name = Column(UnicodeText, nullable=False)
    last_name = Column(UnicodeText, nullable=False)
    email = Column(UnicodeText, nullable=False, unique=True)
    password_hash = Column(UnicodeText, nullable=False)
    password_salt = Column(UnicodeText)
    login_attempts = Column(Integer)
    admin_disabled = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)



    def __init__(self, username, first_name, last_name, email,
                 password_hash, password_salt, login_attempts, admin_disabled,
                 is_superuser=False):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = password_hash
        self.password_salt = password_salt
        self.login_attempts = login_attempts
        self.admin_disabled = admin_disabled
        self.is_superuser = is_superuser

    def __repr__(self):
        return u"<UserProfile(%s)>" % self.username

    @property
    def full_email(self):
        email = '%s %s <%s>' % (self.first_name, self.last_name, self.email)
        return email

    def make_appstruct(self):
        appstruct = {}
        for attr in ('username', 'first_name', 'last_name', 'email'):
            appstruct[attr] = getattr(self, attr)
        return appstruct


class ResetToken(Base):
    __tablename__ = 'reset_tokens'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    username = Column(
        UnicodeText,
        ForeignKey(UserProfile.username),
        index=True,
        nullable=False,
    )
    user = relationship(
        UserProfile,
        primaryjoin='ResetToken.username==UserProfile.username',
        single_parent=True,
        passive_deletes=True,
        uselist=False,
    )
    token = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True,
    )
    came_from = Column(UnicodeText)
    generation_ts = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=FetchedValue(),
        index=True,
    )

    def __init__(self, username, came_from, token=None):
        self.username = username
        self.came_from = came_from
        if token is None:
            token = uuid.uuid4()
        self.token = token

    def __repr__(self):
        return u"<ResetToken(%s)>" % self.token


UPDATE_GENERATION_TS_SQL = """
CREATE OR REPLACE FUNCTION update_generation_ts()
RETURNS TRIGGER AS $$
BEGIN
   NEW.generation_ts = now();
   RETURN NEW;
END;
$$ language 'plpgsql';
"""


def after_tokens_create(target, connection, **kw):
    connection.execute(UPDATE_GENERATION_TS_SQL)
    trigger_sql = """
        CREATE TRIGGER update_token_generation_ts BEFORE UPDATE
        ON %s.%s FOR EACH ROW EXECUTE PROCEDURE
        update_generation_ts();
    """
    connection.execute(trigger_sql % (target.schema, target.name))

event.listen(ResetToken.__table__, "after_create", after_tokens_create)
