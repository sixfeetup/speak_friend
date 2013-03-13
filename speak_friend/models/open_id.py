import datetime
import time

from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import BYTEA

from speak_friend.models import Base

from openid.association import Association as OpenIDAssociation
from openid.store.nonce import SKEW as NONCE_SKEW

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

    @property
    def expires(self):
        """Sets the timestamp for when the current association expires"""
        return self.issued + self.lifetime


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

    def is_expired(self):
        """Checks to see if an association has expired."""
        now = datetime.datetime.now()
        now_stamp = int(time.mktime(now.timetuple()))

        return now_stamp > self.expires

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

    def storeAssociation(self, server_url, raw_association):
        association = Association(
            server_url,
            raw_association.handle,
            raw_association.secret,
            raw_association.issued,
            raw_association.lifetime,
            raw_association.assoc_type,
        )
        self.session.add(association)

    def getAssociation(self, server_url, handle=None):
        query_args = {'server_url': server_url}
        if handle is not None:
            query_args['handle'] = handle
        query = self.session.query(Association)
        expires = func.to_timestamp(Association.issued + Association.lifetime)
        query = query.filter(func.current_timestamp() < expires)
        query = query.filter_by(**query_args)
        query = query.order_by(Association.issued.desc())

        association = query.first()
        if association is None:
            return association

        openid_association = OpenIDAssociation(
            association.handle,
            association.secret,
            association.issued,
            association.lifetime,
            association.assoc_type,
        )
        return openid_association

    def cleanupAssociations(self):
        now = datetime.datetime.now()
        now_stamp = int(time.mktime(now.timetuple()))

        query = self.session.query(Association)
        query = query.filter(Association.issued + Association.lifetime \
                             < now_stamp)
        query.delete()

    def removeAssociation(self, server_url, handle):
        kwargs = {'server_url': server_url, 'handle': handle}
        query = self.session.query(Association)
        num_deleted = query.filter_by(**kwargs).delete()
        return num_deleted > 0

    def useNonce(self, server_url, timestamp, salt):
        past = timestamp - NONCE_SKEW
        future = timestamp + NONCE_SKEW
        query_args = {'server_url': server_url, 'salt': salt}
        query = self.session.query(Nonce).filter_by(**query_args)
        query = query.filter(Nonce.timestamp > past, Nonce.timestamp < future)
        nonces = query.all()

        return not len(nonces) > 0
