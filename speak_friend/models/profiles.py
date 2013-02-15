"""Models for the profiles schema
"""
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import SmallInteger
from sqlalchemy import String

from speak_freind.models import Base


class Domain(Base):
    __tablename__ = 'domain_profiles'
    __table_args__ = (
        {'schema': 'profiles'}
    )
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, length=128)
    password_valid = Column(Integer) # minutes
    max_attempts = Column(SmallInteger)

    def __init__(self, id, name, password_valid, max_attempts):
        self.id = id
        self.name = name
        self.password_valid = password_valid
        self.max_attempts = max_attempts

    def __repr__(self):
        return u'<DomainProfile(%s)>' % self.name
