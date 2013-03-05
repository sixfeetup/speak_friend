from json import loads

from colander import SchemaNode

from pyramid.path import DottedNameResolver
from pyramid.renderers import render_to_response

from sqlalchemy import Column
from sqlalchemy import UnicodeText
import sqlalchemy.types as types

from speak_friend.models import Base


class DottedPath(types.TypeDecorator):
    '''Serializes to JSON on the way in and loads from JSON
    on the way out.
    '''

    impl = types.UnicodeText
    resolver = DottedNameResolver()

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return self.resolver.resolve(value)

    def copy(self):
        return DottedPath(self.impl.length)


class JSON(types.TypeDecorator):
    '''Serializes to JSON on the way in and loads from JSON
    on the way out.
    '''

    impl = types.UnicodeText

    def process_bind_param(self, value, dialect):
        if isinstance(value, SchemaNode):
            json = render_to_response('json', value.serialize()).unicode_body
        elif value is None:
            json = u'null'
        else:
            json = render_to_response('json', value).unicode_body
        return json

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return loads(value)

    def copy(self):
        return JSON(self.impl.length)


class ControlPanelSection(Base):
    __tablename__ = 'control_panel_sections'
    __table_args__ = {'schema': 'settings'}
    section = Column(UnicodeText, primary_key=True)
    panel_path = Column(DottedPath)
    panel_values = Column(JSON)

    def __init__(self, section, panel_path, panel_values):
        self.section = section
        self.panel_path = panel_path
        self.panel_values = panel_values

    def __repr__(self):
        return u"<ControlPanel(%s, %s)>" % (self.section, self.panel_path)

