import datetime

import colander

from pyramid.config import Configurator
from pyramid.config import aslist
from pyramid.exceptions import ConfigurationError
from pyramid.events import BeforeRender
from pyramid.path import DottedNameResolver
from pyramid.renderers import JSON
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from sqlalchemy import engine_from_config

from speak_friend.events import UserActivity
from speak_friend.forms.controlpanel import contact_us_email_notification_schema
from speak_friend.forms.controlpanel import user_creation_email_notification_schema
from speak_friend.models import DBSession, Base
from speak_friend.views import accounts
from speak_friend.views import admin
from speak_friend.views import controlpanel
from speak_friend.views import contactus
from speak_friend.subscribers import register_api
from speak_friend.configuration import add_controlpanel_section
from speak_friend.configuration import set_password_context
from speak_friend.configuration import set_password_validator
from speak_friend.subscribers import log_activity


def datetime_adapter(obj, request):
    return obj.isoformat()


def null_adapter(obj, request):
    return None


def includeme(config):
    # Dependencies
    config.include('deform_bootstrap')
    config.include('pyramid_exclog')
    config.include('pyramid_mailer')

    # Events
    config.add_subscriber(register_api, BeforeRender)
    config.add_subscriber(log_activity, UserActivity)

    # Routes
    config.add_route('create_profile', '/create_profile')
    config.add_view(accounts.create_profile, route_name='create_profile',
                    renderer='templates/create_profile.pt')
    config.add_route('create_domain', '/create_domain')
    config.add_view(admin.create_domain, route_name='create_domain',
                    renderer='templates/create_domain.pt')
    config.add_route('control_panel', '/control_panel')
    config.add_view(controlpanel.ControlPanel,
                    attr="get", request_method='GET',
                    renderer='templates/control_panel.pt')
    config.add_view(controlpanel.ControlPanel,
                    attr="post", request_method='POST',
                    renderer='templates/control_panel.pt')
    config.add_route('contact_us', '/contact_us')
    config.add_view(contactus.ContactUs,
                    attr="get", request_method='GET',
                    renderer='templates/contact_us.pt')
    config.add_view(contactus.ContactUs,
                    attr="post", request_method='POST',
                    renderer='templates/contact_us.pt')
    config.add_static_view('speak_friend_static', 'speak_friend:static',
                           cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')
    config.add_static_view(
        'deform_bootstrap_static', 'deform_bootstrap:static',
        cache_max_age=3600
    )

    # Add custom directives
    config.add_directive('add_controlpanel_section', add_controlpanel_section)
    config.add_directive('set_password_context', set_password_context)

    # Control panel
    ## Necessary JSON adapters, to ensure the data submitted can be serialized
    json_renderer = JSON()
    config.add_renderer('json', json_renderer)
    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    json_renderer.add_adapter(colander.null.__class__, null_adapter)

    ## Add custom directives
    config.add_directive('add_controlpanel_section', add_controlpanel_section)
    config.add_directive('set_password_context', set_password_context)
    config.add_directive('set_password_validator', set_password_validator)

    # Call custom directive
    ## Core control panel sections
    config.add_controlpanel_section(user_creation_email_notification_schema)
    config.add_controlpanel_section(contact_us_email_notification_schema)
    ## Password context
    from passlib.apps import ldap_context
    config.set_password_context(context=ldap_context)
    ## Default password validator
    config.set_password_validator()

    # Session
    settings = config.registry.settings
    session_secret = settings.setdefault('speak_friend.session_secret',
                                         'itsaseekrit')
    session_resolver = DottedNameResolver()
    factory_name = settings.setdefault('speak_friend.session_factory',
                                       'pyramid.session.UnencryptedCookieSessionFactoryConfig')
    factory_class = session_resolver.resolve(factory_name)
    session_factory = factory_class(session_secret)
    config.set_session_factory(session_factory)


def init_sa(config):
    settings = config.registry.settings
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    config.scan('speak_friend.models')
    extra_model_paths = aslist(settings.get('speak_friend.extra_models', []))
    for emp in extra_model_paths:
        config.scan(emp)
    return engine


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    init_sa(config)

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
