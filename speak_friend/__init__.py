import datetime

import colander

import ldap

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.exceptions import ConfigurationError
from pyramid.events import BeforeRender
from pyramid.renderers import JSON

from pyramid_ldap import groupfinder

from sqlalchemy import engine_from_config

from speak_friend.events import UserActivity
from speak_friend.forms.controlpanel import user_creation_email_notification_schema
from speak_friend.models import DBSession, Base
from speak_friend.views import profiles
from speak_friend.views import controlpanel
from speak_friend.subscribers import register_api
from speak_friend.subscribers import log_activity


def datetime_adapter(obj, request):
    return obj.isoformat()

def null_adapter(obj, request):
    return None

def add_controlpanel_section(config, schema, override=False):
    controlpanel = config.registry.setdefault('controlpanel', {})
    if schema.name in controlpanel and not override:
        msg = '%s section already implemented by: %s'
        raise ConfigurationError(msg % (schema.name,
                                        schema.path))
    controlpanel[schema.name] = schema


def includeme(config):
    # Dependencies
    config.include('pyramid_exclog')
    config.include('pyramid_ldap')

    # Events
    config.add_subscriber(register_api, BeforeRender)
    config.add_subscriber(log_activity, UserActivity)

    # Routes
    config.add_route('create_profile', '/create_profile')
    config.add_view(profiles.CreateProfile, attr="get", request_method='GET',
                    renderer='templates/create_profile.pt')
    config.add_view(profiles.CreateProfile, attr="post", request_method='POST',
                    renderer='templates/create_profile.pt')
    config.add_route('control_panel', '/control_panel')
    config.add_view(controlpanel.control_panel, route_name='control_panel',
                    renderer='templates/control_panel.pt')
    config.add_static_view('speak_friend_static', 'speak_friend:static', cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')

    config.set_authentication_policy(
        AuthTktAuthenticationPolicy(config.registry.settings['auth_secret'],
                                   callback=groupfinder,
                                   hashalg='sha512')
    )
    config.set_authorization_policy(
        ACLAuthorizationPolicy()
    )

    ldap_cache = config.registry.settings.get('speak_friend.ldap_cache_period', 0)
    config.ldap_setup(
        config.registry.settings['speak_friend.ldap_server'],
        bind=config.registry.settings['speak_friend.ldap_user_cn'],
        passwd=config.registry.setting['speak_friend.ldap_password']
    )

    config.ldap_set_login_query(
        base_dn=config.registry.settings['speak_friend.ldap_base_people_dn'],
        filter_tmpl=config.registry.settings.get('speak_friend.ldap_people_filter_tmpl',
                                                 '(uid=%(login)s)'),
        scope = ldap.SCOPE_ONELEVEL,
        cache_period=ldap_cache,
    )

    config.ldap_set_groups_query(
        base_dn=config.registry.settings['speak_friend.ldap_base_group_dn'],
        filter_tmpl=config.registry.settings('speak_friend.ldap_group_filter_tmpl',
                                            '(&(objectCategory=group)(member=%(userdn)s))'),
        scope=ldap.SCOPE_SUBTREE,
        cache_period=ldap_cache,
    )

    # Control panel
    ## Necessary JSON adapters, to ensure the data submitted can be serialized
    json_renderer = JSON()
    config.add_renderer('json', json_renderer)
    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    json_renderer.add_adapter(colander.null.__class__, null_adapter)
    ## Add custom directives
    config.add_directive('add_controlpanel_section', add_controlpanel_section)
    ## And call with our notification form
    config.add_controlpanel_section(user_creation_email_notification_schema)


def init_sa(settings):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    init_sa(settings)

    # Includes for any packages that hook into configuration.
    config.include('pyramid_tm')

    # Extending an existing package allows you to override
    # view mappings and other configuration details.
    # config.include('base_package_name')

    # overriding templates should be done as follows:

    # config.override_asset('base_package_name:templates/base.pt',
    #                       'speak_friend:templates/override.pt')

    # Configuring URLs
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    includeme(config)
    config.scan()

    return config.make_wsgi_app()
