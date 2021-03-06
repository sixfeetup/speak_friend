from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.security import authenticated_userid
from speak_friend.models.profiles import UserProfile
from speak_friend.oauth_provider import SFOauthProvider
from speak_friend.forms.oauth2_api import make_client_authorization_form


# add secret to domain profile
def create_secret(context, request):
    '''Generate and display a new secret for the client application'''
    if request.method != 'POST':
        return HTTPMethodNotAllowed()
    provider = SFOauthProvider(request.db_session)
    client_id = request.POST.get('domain', '')
    domain = provider.domain_with_id(client_id)
    secret = provider.create_client_secret(domain)
    return {
        'domain': domain.name,
        'display_name': domain.display_name,
        'plain_secret': secret,
    }


# OAuth2 authentication views
def authorize_client(context, request):
    '''Request permission for the application to act as the user'''
    provider = SFOauthProvider(request.db_session)
    client_id = request.GET.get('domain', '')
    redirect_uri = request.GET.get('redirect_uri', '')
    response_type = request.GET.get('response_type', 'code')
    # store in the session for 'process_authorization' below
    request.session['oauth2_redirect_uri'] = redirect_uri
    request.session['oauth2_client_id'] = client_id
    request.session['oauth2_response_type'] = response_type
    valid = provider.validate_redirect_uri(
        request,
        redirect_uri
    )
    if valid:
        domain = provider.domain_with_id(client_id)
        form = make_client_authorization_form(request)
        form.action = request.route_url('process_authorization')
        form_html = form.render()
        return {
            'domain': domain.name,
            'display_name': domain.display_name,
            'form_html': form_html,
        }
    return HTTPForbidden('Redirect URL not valid for referring domain')


def process_authorization(context, request):
    '''Send a temporary authorization code to the client application'''
    response_type = request.session.get('oauth2_response_type', 'code')
    if response_type == 'token':
        loc_template = '{redirect_uri}#token={code}'
    else:
        loc_template = '{redirect_uri}?code={code}'
    allowed = 'submit' in request.POST
    if allowed:
        # user allowed access
        provider = SFOauthProvider(request.db_session)
        username = authenticated_userid(request)
        client_id = request.session.get('oauth2_client_id', '')
        try:
            if response_type == 'token':
                # place-holder auth code for direct token requests
                transient_code = provider.generate_authorization_code()
                response_code = provider.generate_access_token()
                provider.persist_authorization_code(
                    client_id, username, transient_code
                )
                provider.persist_access_token(
                    client_id, transient_code, response_code
                )
            else:
                response_code = provider.generate_authorization_code()
                provider.persist_authorization_code(
                    client_id, username, response_code
                )
        except:
            return HTTPInternalServerError()
    else:
        response_code = 'none'
    params = {
        'code': response_code,
        'redirect_uri': request.session.get('oauth2_redirect_uri', ''),
    }
    loc = loc_template.format(**params)
    return HTTPFound(location=loc)


def request_access_token(context, request):
    '''authenticate client app and provide a token'''
    if request.method != 'POST':
        return HTTPMethodNotAllowed()
    provider = SFOauthProvider(request.db_session)
    client_id = request.POST.get('domain', '')
    client_secret = request.POST.get('secret', '')
    request_auth_code = request.matchdict['code']
    client_valid = provider.validate_client_secret(client_id, client_secret)
    code_valid = provider.validate_auth_code(client_id, request_auth_code)
    if client_valid and code_valid:
        token = provider.generate_access_token()
        try:
            provider.persist_access_token(client_id, request_auth_code, token)
        except:
            request.reponse.status = 500
            return {'error': 'database error'}
        return {'access_token': token}
    else:
        request.response.status = 403
        return {'error': 'request for authentication token denied'}


# resource views
def get_user_details(context, request):
    '''validate the application and return user details'''
    if request.method != 'POST':
        return HTTPMethodNotAllowed()
    provider = SFOauthProvider(request.db_session)
    client_id = request.POST.get('domain', '')
    token = request.POST.get('token', '')
    username = provider.user_for_access_token(client_id, token)
    if not username:
        request.response.status = 403
        return {'error': 'access token not valid for domain'}
    user = request.db_session.query(UserProfile).get(username)
    if user:
        request.response.headers['Access-Control-Allow-Method'] = 'POST'
        request.response.headers['Access-Control-Allow-Origin'] = '*'
        return {
            'username': username,
            'email': user.email,
            'given_name': user.first_name,
            'surname': user.last_name,
        }
    request.response.status = 404
    return {'error': 'user not found'}


def validate_user_token(context, request):
    '''validate a user using an access token'''
    if request.method != 'POST':
        return HTTPMethodNotAllowed()
    provider = SFOauthProvider(request.db_session, tokens_expire=False)
    username = request.POST.get('user', '')
    token = request.POST.get('token', '')
    try:
        valid = provider.validate_user_with_access_token(username, token)
    except:
        valid = False
    return {'valid': valid}
