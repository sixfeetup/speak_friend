from datetime import datetime, timedelta
import logging

from openid.extensions import sreg
from openid.server.server import Server
from openid.consumer import discover

from psycopg2.tz import FixedOffsetTimezone

from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.security import authenticated_userid
from pyramid.view import view_defaults


from speak_friend.forms.controlpanel import MAX_PASSWORD_VALID
from speak_friend.models.open_id import SFOpenIDStore
from speak_friend.models.profiles import DomainProfile
from speak_friend.models.profiles import UserProfile
from speak_friend.utils import get_domain
from speak_friend.utils import get_referrer
from speak_friend.views.accounts import logout


logger = logging.getLogger('speak_friend.openid_provider')

@view_defaults(route_name='openid_provider')
class OpenIDProvider(object):
    # OpenID service type URIs, listed in order of preference.  The
    # ordering of this list affects yadis and XRI service discovery.
    openid_type_uris = [
        #discover.OPENID_IDP_2_0_TYPE,
        discover.OPENID_2_0_TYPE,
        discover.OPENID_1_1_TYPE,
        discover.OPENID_1_0_TYPE,
        sreg.ns_uri,
    ]

    def __init__(self, request):
        self.request = request
        self.openid_server = Server(SFOpenIDStore(self.request.db_session),
                                    request.route_url('openid_provider'))
        self.auth_userid = authenticated_userid(request)
        if self.auth_userid:
            query = self.request.db_session.query(UserProfile)
            self.auth_user = query.get(self.auth_userid)
        else:
            self.auth_user = None

    def checkPasswordTimeout(self, now=None):
        """Verify the last login timestamp is still valid.
        Expects datetime.utcnow()
        """
        domain_name = get_domain(self.request)
        domain = self.request.db_session.query(DomainProfile).get(domain_name)
        if domain:
            pw_valid = timedelta(minutes=domain.get_password_valid())
        else:
            pw_valid = timedelta(minutes=MAX_PASSWORD_VALID)

        if now is None:
            now = datetime.utcnow()
        utc_now = now.replace(tzinfo=FixedOffsetTimezone(offset=0))
        if self.request.user:
            last_login = self.request.user.last_login(self.request.db_session)
            return last_login + pw_valid > utc_now
        else:
            # Not enough info to apply policy
            logger.debug('Password timeout passed, no user')
            return True

    def process(self, request_params):
        logger.debug('Processing openid request: %s', request_params)
        if not self.checkPasswordTimeout():
            logger.debug('Password timeout: %s', self.request.user)
            return_to = self.request.route_url('home')
            return logout(self.request, return_to)

        openid_request = self.openid_server.decodeRequest(request_params)
        logger.debug('Decoded request: %s', openid_request)
        if openid_request is None:
            return ''

        if openid_request.mode in ["checkid_immediate", "checkid_setup"]:
            openid_response = self.handleCheckIDRequest(openid_request)
        else:
            openid_response = self.openid_server.handleRequest(openid_request)
        logger.debug('Decoded response: %s', openid_response)
        encoded_response = self.openid_server.encodeResponse(openid_response)

        if 'location' in encoded_response.headers:
            response = HTTPFound(location=encoded_response.headers['location'])
            return response
        return encoded_response.body

    def get(self):
        return self.process(self.request.GET)

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        return self.process(self.request.POST)

    def approved(self, request, identifier=None):
        response = request.answer(True, identity=identifier)
        self.addSRegResponse(request, response)
        return response

    def handleCheckIDRequest(self, request):
        is_authorized = self.isAuthorized(request.identity, request.trust_root)
        if is_authorized:
            return self.approved(request, request.identity)
        else:
            return request.answer(False, identity=request.identity)

    def isAuthorized(self, identity_url, trust_root):
        if not self.auth_userid:
            return False

        # TODO: prompt user for authorization
        return True

    def addSRegResponse(self, request, response):
        sreg_req = sreg.SRegRequest.fromOpenIDRequest(request)
        sreg_data = dict([
            (fname, None)
            for fname in sreg.data_fields
        ])
        sreg_data['fullname'] = '%s %s' % (self.auth_user.first_name,
                                           self.auth_user.last_name)
        sreg_data['nickname'] = self.auth_userid
        sreg_data['email'] = self.auth_user.email
        sreg_resp = sreg.SRegResponse.extractResponse(sreg_req, sreg_data)
        response.addExtension(sreg_resp)


@view_defaults(route_name='yadis')
def generate_xrds(request):
    auth_userid = authenticated_userid(request)
    identity_url = request.route_url('user_profile', username=auth_userid)
    return {
        'auth_userid': auth_userid,
        'identity_url': identity_url,
        'services': OpenIDProvider.openid_type_uris,
    }
