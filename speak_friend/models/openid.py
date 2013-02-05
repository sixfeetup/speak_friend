from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy.dialects.postgresql import BYTEA
from speak_friend.models import Base

from zope.interface import implements

from speak_friend.interfaces import IOpenIDStore
from speak_friend.models import DBSession


class Association(Base):
    __tablename__ = 'associations'
    __table_args__ = {'schema': 'openid'}
    server_url = Column(UnicodeText, primary_key=True)
    handle = Column(UnicodeText, primary_key=True)
    secret = Column(BYTEA(length=128))
    issued = Column(Integer)
    lifetime = Column(Integer)
    assoc_type = Column(UnicodeText)

    def __init__(self, server_url, handle, secret,
                 issued, lifetime, assoc_type):
        self.server_url = server_url
        self.handle = handle
        self.secret = secret
        self.issued = issued
        self.lifetime = lifetime
        self.assoc_type = assoc_type

    def __repr__(self):
        return u"<Association(%s, %s)>" % (self.server_url, self.handle)

class Nonce(Base):
    __tablename__ = 'nonces'
    __table_args__ = {'schema': 'openid'}
    schema = 'openid'
    server_url = Column(UnicodeText, primary_key=True)
    timestamp = Column(Integer, primary_key=True)
    salt = Column(UnicodeText, primary_key=True)

    def __init__(self, server_url, timestamp, salt):
        self.server_url = server_url
        self.timestamp = timestamp
        self.salt = salt

    def __repr__(self):
        return u"<Nonce(%s)>" % self.server_url


class SFOpenIDStore(object):
    implements(IOpenIDStore)

    def __init__(self, session):
        self.session = session

    def storeAssociation(self, server_url, association):
        self.session.add(association)
        self.session.commit()

    def getAssociation(self, server_url, handle=None):
        association = self.session.query.filter_by(server_url=server_url).first()
        return association

    def removeAssociation(self, server_url, handle):
        pass

    def useNonce(self, server_url, timestamp, salt):
        pass
