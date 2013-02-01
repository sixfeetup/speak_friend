from sqlalchemy import Integer, UnicodeText
from sqlalchemy.dialects.postgresql import BYTEA
from speak_friend.models import Base


class Association(Base):
    __tablename__ = 'associations'
    server_url = UnicodeText(primary_key=True)
    handle = UnicodeText(primary_key=True)
    secret = BYTEA(length=128)
    issued = Integer()
    lifetime = Integer()
    assoc_type = UnicodeText()


class Nonce(Base):
    __tablename__ = 'nonces'
    server_url = UnicodeText(primary_key=True)
    timestamp = Integer(primary_key=True)
    salt = UnicodeText(primary_key=True)

