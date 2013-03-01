from ldappool import ConnectionManager
from pyramid_ldap import Connector

# The connection manager and connector utility functions are separated
# because there are LDAP operations (like editing a user CN) that require
# a connection manager, but not the connector


def get_connection_manager(settings):
    """Creates an LDAP pool ConnectionManager object from app settings"""
    uri = settings['speak_friend.ldap_server']
    bind_cn = settings['speak_friend.ldap_user_cn']
    bind_passwd = settings['speak_friend.ldap_password']
    cm = ConnectionManager(uri, bind=bind_cn, passwd=bind_passwd)
    return cm


def get_connector(registry, connection_manager):
    """Creates a pyramid_ldap Connector"""
    connector = Connector(registry, connection_manager)
    return connector
