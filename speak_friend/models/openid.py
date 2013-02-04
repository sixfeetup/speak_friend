from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy.dialects.postgresql import BYTEA
from speak_friend.models import Base

from zope.interface import implements

from speak_friend.interfaces import IOpenIDStore


class Association(Base):
    __tablename__ = 'associations'
    __table_args__ = {'schema': 'openid'}
    server_url = Column(UnicodeText, primary_key=True)
    handle = Column(UnicodeText, primary_key=True)
    secret = Column(BYTEA(length=128))
    issued = Column(Integer)
    lifetime = Column(Integer)
    assoc_type = Column(UnicodeText)


class Nonce(Base):
    __tablename__ = 'nonces'
    __table_args__ = {'schema': 'openid'}
    schema = 'openid'
    server_url = Column(UnicodeText, primary_key=True)
    timestamp = Column(Integer, primary_key=True)
    salt = Column(UnicodeText, primary_key=True)


class SFOpenIDStore(object):
    implements(IOpenIDStore)

    def storeAssociation(self, server_url, association):
        pass

    def getAssociation(self, server_url, handle=None):
        pass

    def removeAssociation(self, server_url, handle):
        pass

    def useNonce(self, server_url, timestamp, salt):
        pass
