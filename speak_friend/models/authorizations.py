from sqlalchemy import Column
from sqlalchemy import TIMESTAMP
from sqlalchemy import UnicodeText

from sixfeetup.bowab.db import Base


class OAuthAuthorization(Base):
    __tablename__ = 'oauth_authorizations'
    username = Column(UnicodeText, primary_key=True, nullable=False)
    client_id = Column(UnicodeText, primary_key=True, nullable=False)
    access_token = Column(UnicodeText, nullable=False)
    auth_code = Column(UnicodeText, nullable=True)
    valid_until = Column(TIMESTAMP, nullable=False)

    def __init__(self, username, client_id,
                 access_token, auth_code, valid_until):
        self.username = username
        self.client_id = client_id
        self.access_token = access_token
        self.auth_code = auth_code
        self.valid_until = valid_until
