from datetime import datetime, timedelta
import logging

from psycopg2.tz import FixedOffsetTimezone

from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response

from sqlalchemy.orm.exc import DetachedInstanceError

from speak_friend.forms.controlpanel import MAX_DOMAIN_ATTEMPTS
from speak_friend.forms.controlpanel import MAX_PASSWORD_VALID
from speak_friend.models.profiles import DomainProfile
from speak_friend.models.reports import UserActivity
from speak_friend.utils import get_domain
from speak_friend.views.controlpanel import ControlPanel
from speak_friend.views.accounts import logout
from speak_friend.views.accounts import LoginView
from speak_friend.views.open_id import OpenIDProvider


def password_timeout_factory(handler, registry):
    # TODO: refactor this as a custom authn, with different cookies per domain?
    def password_timeout_tween(request):
        """Verify the last login timestamp is still valid.
        """
        logger = logging.getLogger('speakfriend.password_timeout_tween')
        response = handler(request)

        if not request.user:
            return response

        cp = ControlPanel(request)
        domain_name = get_domain(request)
        domain = request.db_session.query(DomainProfile).get(domain_name)
        if domain:
            pw_valid = timedelta(minutes=domain.get_password_valid(cp))
        else:
            pw_valid = timedelta(minutes=MAX_PASSWORD_VALID)

        now = datetime.utcnow()
        utc_now = now.replace(tzinfo=FixedOffsetTimezone(offset=0))
        try:
            last_login = request.user.last_login(request.db_session)
        except DetachedInstanceError:
            request.db_session.add(request.user)
            last_login = request.user.last_login(request.db_session)
        if last_login and last_login.activity_ts + pw_valid < utc_now:
            msg = 'You must log in again to be returned to: %s' % domain_name
            request.session.flash(msg, queue='error')
            logger.info('Password validity time out: %r, %r, %s',
                       request.user, last_login, pw_valid)
            response = logout(request, request.route_url('home'))

        return response

    return password_timeout_tween


def initial_login_factory(handler, registry):
    def initial_login_tween(request):
        """Verify the user has logged into a referring site at least once.
        """
        response = handler(request)
        if not request.user:
            return response
        logger = logging.getLogger('speak_friend.initial_login_tween')
        domain_name = get_domain(request)
        now = datetime.utcnow()
        utc_now = now.replace(tzinfo=FixedOffsetTimezone(offset=0))
        try:
            query = request.user.activity_query(request.db_session,
                                                u'login')
        except DetachedInstanceError:
            request.db_session.add(request.user)
            query = request.user.activity_query(request.db_session,
                                                u'login')
        query = query.filter(UserActivity.came_from_fqdn == domain_name)
        domain_logins = query.count()
        local_request = request.host.startswith(domain_name)
        if domain_logins == 0 and not local_request:
            logger.info('User has not logged in from here yet: %r, %s',
                        request.user, domain_name)
            msg = 'You must log in again to be returned to: %s' % domain_name
            request.session.flash(msg, queue='error')
            request.session.changed()
            response = logout(request, request.route_url('home'))

        return response

    return initial_login_tween


def openid_factory(handler, registry):
    def openid_tween(request):
        """Verify the user has logged into a referring site at least once.
        """
        response = handler(request)
        if 'openid_request' in request.session and \
           'auth_userid' in request.session:
            provider = OpenIDProvider(request)
            openid_response = provider.process(request.session['openid_request'])
            response.location = openid_response.location
            del request.session['auth_userid']
            del request.session['openid_request']

        return response

    return openid_tween


def user_disabled_factory(handler, registry):
    def user_disabled_tween(request):
        """Verify the user has not been disabled.
        """
        logger = logging.getLogger('speakfriend.user_disabled_tween')

        if not request.user:
            return handler(request)

        if request.user.admin_disabled:
            login = LoginView(request, MAX_DOMAIN_ATTEMPTS)
            request.session.flash(login.disabled_error, queue='error')
            logger.info('User logged out because of admin_disabled: %s',
                        request.user)
            response = logout(request)
        else:
            response = handler(request)

        return response

    return user_disabled_tween


def valid_referrer_factory(handler, registry):
    def valid_referrer_tween(request):
        """Verify the referring domain is valid.
        """
        logger = logging.getLogger('speakfriend.valid_referrer_tween')

        response = handler(request)

        if 'location' in response.headers:
            domain_name = get_domain(response.headers['location'])
            domain = request.db_session.query(DomainProfile).get(domain_name)
            if domain is None:
                msg = 'Invalid requesting domain, not redirecting: %s' % domain_name
                request.session.flash(msg, queue='error')
                response.headers.pop('location')
                response = HTTPFound(request.route_url('home'),
                                     headers=response.headers)

        return response

    return valid_referrer_tween
