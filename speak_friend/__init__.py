import datetime

import colander

from openid.yadis.constants import YADIS_CONTENT_TYPE

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.config import aslist
from pyramid.exceptions import ConfigurationError
from pyramid.events import BeforeRender
from pyramid.events import NewResponse
from pyramid.path import DottedNameResolver
from pyramid.renderers import JSON
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from sqlalchemy import engine_from_config

from speak_friend.configuration import add_controlpanel_section
from speak_friend.configuration import get_user
from speak_friend.configuration import set_password_context
from speak_friend.configuration import set_password_validator
from speak_friend.events import AccountCreated
from speak_friend.events import UserActivity
from speak_friend.forms.controlpanel import contact_us_email_notification_schema
from speak_friend.forms.controlpanel import password_reset_schema
from speak_friend.forms.controlpanel import user_creation_email_notification_schema
from speak_friend.forms.controlpanel import domain_defaults_schema
from speak_friend.models import DBSession, Base
from speak_friend.security import userfinder
from speak_friend.views import accounts
from speak_friend.views import admin
from speak_friend.views import controlpanel
from speak_friend.views import contactus
from speak_friend.views import open_id
from speak_friend.subscribers import confirm_account_created
from speak_friend.subscribers import handle_openid_request
from speak_friend.subscribers import log_activity
from speak_friend.subscribers import notify_account_created
from speak_friend.subscribers import register_api


def datetime_adapter(obj, request):
    return obj.isoformat()


def null_adapter(obj, request):
    return None


def includeme(config):
    # Dependencies
    config.include('deform_bootstrap')
    config.include('pyramid_exclog')
    config.include('pyramid_mailer')

    # Authz/Authn
    authn_secret = config.registry.settings.get('speak_friend.authn_secret',
                                                'this is bad')
    authn_policy = AuthTktAuthenticationPolicy(secret=authn_secret,
                                               callback=userfinder
    )
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)
    config.set_authentication_policy(authn_policy)

    # Events
    config.add_subscriber(register_api, BeforeRender)
    config.add_subscriber(handle_openid_request, NewResponse)
    config.add_subscriber(log_activity, UserActivity)
    config.add_subscriber(confirm_account_created, AccountCreated)
    config.add_subscriber(notify_account_created, AccountCreated)

    # Routes
    config.add_route('yadis', '/yadis.xml')
    config.add_view(open_id.generate_xrds, accept=YADIS_CONTENT_TYPE,
                    route_name='yadis',
                    renderer='templates/xrds.pt')
    config.add_route('openid_provider', '/server')
    config.add_view(open_id.OpenIDProvider, attr="get", request_method='GET',
                    route_name='openid_provider',
                    renderer='templates/openid_response.pt')
    config.add_view(open_id.OpenIDProvider, attr="post", request_method='POST',
                    route_name='openid_provider',
                    renderer='templates/openid_response.pt')
    config.add_route('create_profile', '/create_profile')
    config.add_view(accounts.CreateProfile, attr="get", request_method='GET',
                    route_name='create_profile',
                    renderer='templates/create_profile.pt')
    config.add_view(accounts.CreateProfile, attr="post", request_method='POST',
                    route_name='create_profile',
                    renderer='templates/create_profile.pt')
    config.add_route('edit_profile', '/edit_profile/{username}/')
    config.add_view(accounts.EditProfile, attr="get", request_method='GET',
                    route_name='edit_profile',
                    renderer='templates/edit_profile.pt')
    config.add_view(accounts.EditProfile, attr="post", request_method='POST',
                    route_name='edit_profile',
                    renderer='templates/edit_profile.pt')
    config.add_route('token_expired', '/token_expired')
    config.add_view(accounts.token_expired, route_name='token_expired',
                    renderer='templates/token_expired.pt')
    config.add_route('request_password', '/request_password')
    config.add_view(accounts.RequestPassword,
                    route_name='request_password',
                    attr="get", request_method='GET',
                    renderer='templates/request_password.pt')
    config.add_view(accounts.RequestPassword,
                    attr="post", request_method='POST',
                    route_name='request_password',
                    renderer='templates/request_password.pt')
    config.add_route('reset_password', '/reset_password/{token}')
    config.add_view(accounts.ResetPassword,
                    attr="get", request_method='GET',
                    route_name='reset_password',
                    renderer='templates/reset_password.pt')
    config.add_view(accounts.ResetPassword,
                    attr="post", request_method='POST',
                    route_name='reset_password',
                    renderer='templates/reset_password.pt')
    config.add_route('create_domain', '/create_domain')
    config.add_view(admin.CreateDomain, attr="get", request_method='GET',
                    route_name='create_domain',
                    renderer='templates/create_domain.pt')
    config.add_view(admin.CreateDomain, attr='post', request_method='POST',
                    route_name='create_domain',
                    renderer='templates/create_domain.pt')
    config.add_route('control_panel', '/control_panel')
    config.add_view(controlpanel.ControlPanel,
                    route_name='control_panel',
                    attr="get", request_method='GET',
                    renderer='templates/control_panel.pt')
    config.add_view(controlpanel.ControlPanel,
                    attr="post", request_method='POST',
                    route_name='control_panel',
                    renderer='templates/control_panel.pt')
    config.add_route('contact_us', '/contact_us')
    config.add_view(contactus.ContactUs,
                    attr="get", request_method='GET',
                    route_name='contact_us',
                    renderer='templates/contact_us.pt')
    config.add_view(contactus.ContactUs,
                    attr="post", request_method='POST',
                    route_name='contact_us',
                    renderer='templates/contact_us.pt')
    config.add_route('login', '/login')
    config.add_view(accounts.LoginView, attr='get', request_method='GET',
                    route_name='login',
                    renderer='templates/login.pt')
    config.add_view(accounts.LoginView, attr='post', request_method='POST',
                    route_name='login',
                    renderer='templates/login.pt')
    config.add_route('logout', '/logout')
    config.add_view(accounts.logout, route_name='logout')
    config.add_static_view('speak_friend_static', 'speak_friend:static',
                           cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')
    config.add_static_view(
        'deform_bootstrap_static', 'deform_bootstrap:static',
        cache_max_age=3600
    )
    # Put last, so that app routes are not swallowed
    config.add_route('user_profile', '/{username}')
    # by providing this override, we create a search path for static assets
    # that first looks in the speak_friend static directory, and then moves
    # to the deform static directory if an asset is not found.
    config.override_asset(to_override='deform:static/',
                          override_with='speak_friend:static/')

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

    # Call custom directives
    ## Core control panel sections
    config.add_controlpanel_section(contact_us_email_notification_schema)
    config.add_controlpanel_section(password_reset_schema)
    config.add_controlpanel_section(user_creation_email_notification_schema)
    config.add_controlpanel_section(domain_defaults_schema)
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
    config.add_request_method(get_user, 'user', reify=True)


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
