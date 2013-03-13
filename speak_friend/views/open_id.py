from openid.extensions import sreg
from openid.server.server import Server
from openid.consumer import discover

import transaction

from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.security import authenticated_userid
from pyramid.view import view_defaults

from speak_friend.models import DBSession
from speak_friend.models.open_id import SFOpenIDStore
from speak_friend.models.profiles import UserProfile


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
        self.session = DBSession()
        self.openid_server = Server(SFOpenIDStore(self.session),
                                    request.route_url('openid_provider'))
        self.auth_userid = authenticated_userid(request)
        if self.auth_userid:
            query = self.session.query(UserProfile)
            self.auth_user = query.get(self.auth_userid)
        else:
            self.auth_user = None

    def get(self):
        openid_request = self.openid_server.decodeRequest(self.request.GET)
        if openid_request.mode in ["checkid_immediate", "checkid_setup"]:
            openid_response = self.handleCheckIDRequest(openid_request)
        else:
            openid_response = self.openid_server.handleRequest(openid_request)
        encoded_response = self.openid_server.encodeResponse(openid_response)
        if 'location' in encoded_response.headers:
            response = HTTPFound(location=encoded_response.headers['location'])
            transaction.commit()
            return response

        return {
            'encoded_response': encoded_response,
            'openid_response': encoded_response.body,
        }

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        openid_request = self.openid_server.decodeRequest(self.request.POST)
        if openid_request.mode in ["checkid_immediate", "checkid_setup"]:
            openid_response = self.handleCheckIDRequest(openid_request)
        else:
            openid_response = self.openid_server.handleRequest(openid_request)
        encoded_response = self.openid_server.encodeResponse(openid_response)
        if 'location' in encoded_response.headers:
            response = HTTPFound(location=encoded_response.headers['location'])
            transaction.commit()
            return response
        return {
            'encoded_response': encoded_response,
            'openid_response': encoded_response.body,
        }

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
