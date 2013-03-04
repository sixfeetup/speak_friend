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
from sqlalchemy import types
from sqlalchemy.ext.compiler import compiles
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


class tsvector(types.TypeDecorator):
    impl = types.UnicodeText


@compiles(tsvector, 'postgresql')
def compile_tsvector(element, compiler, **kw):
    return 'tsvector'

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    username = Column(UnicodeText, primary_key=True)
    first_name = Column(UnicodeText)
    last_name = Column(UnicodeText)
    email = Column(UnicodeText, nullable=False, unique=True)
    password_hash = Column(UnicodeText)
    password_salt = Column(UnicodeText)
    login_attempts = Column(Integer)
    admin_disabled = Column(Boolean, default=False)
    searchable_text = Column(tsvector)


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


FT_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION user_searchable_text_trigger()
RETURNS trigger AS $$
begin
  new.searchable_text :=
    setweight(to_tsvector(coalesce(new.username, '')), 'D') ||
    setweight(to_tsvector(coalesce(new.email, '')), 'C') ||
    setweight(to_tsvector(coalesce(new.first_name, '')), 'B') ||
    setweight(to_tsvector(coalesce(new.last_name, '')), 'A');
  return new;
end
$$ LANGUAGE plpgsql;
"""
FT_INDEX = """
CREATE INDEX user_searchable_text_index ON %s.%s USING gin(searchable_text)
"""
FT_TRIGGER = """
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
    ON %s.%s FOR EACH ROW EXECUTE PROCEDURE user_searchable_text_trigger();
"""


def after_user_profile_create(target, connection, **kw):
    connection.execute(FT_TRIGGER_FUNCTION)
    connection.execute(FT_TRIGGER % (target.schema, target.name))
    connection.execute(FT_INDEX % (target.schema, target.name))


event.listen(UserProfile.__table__, "after_create", after_user_profile_create)


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
        server_onupdate=FetchedValue(),
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
