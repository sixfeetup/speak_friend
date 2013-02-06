"""Models for the profiles schema
"""
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import SmallInteger
from sqlalchemy import String

from speak_freind.models import Base


class Domain(Base):
    __tablename__ = "domains"
    __table_args__ = {'schema': 'profiles'}
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, length=128)
    password_valid = Column(Integer) # minutes, seconds, hours, days??
    max_attempts = Column(SmallInteger)
