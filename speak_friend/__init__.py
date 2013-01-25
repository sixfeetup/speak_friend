from pyramid.config import Configurator
from pyramid.events import BeforeRender

from speak_friend.views import accounts
from speak_friend.subscribers import register_api



def includeme(config):
    # Placeholder for now.
    config.add_route('create_account', '/create_account')
    config.add_view(accounts.create_account, route_name='create_account',
                    renderer='templates/create_account.pt')
    config.add_subscriber(register_api, BeforeRender)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

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
