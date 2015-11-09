# largely based on https://github.com/NateFerrero/oauth2lib
import datetime
from speak_friend.models.authorizations import OAuthAuthorization
from speak_friend.models.profiles import DomainProfile
from speak_friend.models.profiles import UserProfile
from speak_friend.utils import get_domain
from speak_friend.utils import hash_string
from speak_friend.utils import random_ascii_string


UNDEFINED_SECRET = 'TBD'


class SFOauthProvider(object):
    token_length = 64
    token_expires_in = 10  # days
    auth_code_expires_in = 3  # minutes

    def __init__(self, db_session=None, tokens_expire=True):
        self.db_session = db_session
        self.tokens_expire = tokens_expire

    @property
    def token_expiration(self):
        now = datetime.datetime.utcnow()
        return now + datetime.timedelta(days=self.token_expires_in)

    @property
    def auth_code_expiration(self):
        now = datetime.datetime.utcnow()
        return now + datetime.timedelta(minutes=self.auth_code_expires_in)

    def domain_with_id(self, client_id):
        """get the record for this domain by ID"""
        return self.db_session.query(
            DomainProfile
        ).filter(
            DomainProfile.name == client_id
        ).first()

    def generate_authorization_code(self):
        """Generate a random authorization code."""
        return random_ascii_string(self.token_length)

    def generate_access_token(self):
        """Generate a random access token."""
        return random_ascii_string(self.token_length)

    def validate_client_id(self, client_id):
        """Is a domain with this ID registered?"""
        domain = self.domain_with_id(client_id)
        return bool(domain)

    def create_client_secret(self, domain):
        """Generate and store a random string"""
        if domain:
            client_secret = random_ascii_string(32)
            domain.client_secret = hash_string(client_secret)
            return client_secret

    def validate_client_secret(self, client_id, client_secret):
        """Is the secret correct for this domain?"""
        domain = self.db_session.query(
            DomainProfile.name,
            DomainProfile.client_secret,
        ).filter(
            DomainProfile.name == client_id
        ).first()
        hashed = hash_string(client_secret)
        return (domain.client_secret == hashed)

    def validate_redirect_uri(self, request, redirect_uri):
        # redirect URL must be part of a registered domain
        # redirect domain must match referrer domain
        req_domain_name = get_domain(request)
        rdr_domain_name = get_domain(redirect_uri)
        domain = DomainProfile.apply_wildcard(request.db_session,
                                              req_domain_name)
        return (domain and req_domain_name == rdr_domain_name)

    def persist_authorization_code(self, client_id, username, code):
        authz = self.db_session.query(OAuthAuthorization).filter(
            OAuthAuthorization.client_id == client_id,
            OAuthAuthorization.username == username,
        ).first()
        if authz:
            # update the row
            authz.access_token = UNDEFINED_SECRET
            authz.auth_code = code
            authz.valid_until = self.auth_code_expiration
        else:
            # create a row
            new_authz = OAuthAuthorization(
                username=username,
                client_id=client_id,
                access_token=UNDEFINED_SECRET,
                auth_code=code,
                valid_until=self.auth_code_expiration,
            )
            self.db_session.add(new_authz)

    def persist_access_token(self, client_id, auth_code, token):
        # throw away auth code, store access token, extend expiration
        authz = self.db_session.query(OAuthAuthorization).filter(
            OAuthAuthorization.client_id == client_id,
            OAuthAuthorization.auth_code == auth_code,
        ).first()
        authz.auth_code = UNDEFINED_SECRET
        authz.access_token = token
        authz.valid_until = self.token_expiration

    def validate_auth_code(self, client_id, auth_code):
        """Look for an authorization based on auth code and domain"""
        if len(auth_code) < self.token_length or auth_code == UNDEFINED_SECRET:
            return False
        now = datetime.datetime.utcnow()
        authz = self.db_session.query(OAuthAuthorization).filter(
            OAuthAuthorization.client_id == client_id,
            OAuthAuthorization.auth_code == auth_code,
            OAuthAuthorization.valid_until > now,
        ).first()
        return bool(authz)

    def _authorization_for_access_token(self, client_id, token):
        """Look for an authorization based on token and domain"""
        if len(token) < self.token_length or token == UNDEFINED_SECRET:
            return False
        if self.tokens_expire:
            now = datetime.datetime.utcnow()
        else:
            now = datetime.datetime.utcfromtimestamp(0)
        authz = self.db_session.query(OAuthAuthorization).filter(
            OAuthAuthorization.client_id == client_id,
            OAuthAuthorization.access_token == token,
            OAuthAuthorization.valid_until > now,
        ).first()
        return authz

    def user_for_access_token(self, client_id, token):
        """return the username associated with the authorization"""
        authz = self._authorization_for_access_token(client_id, token)
        if authz:
            return authz.username

    def validate_user_with_access_token(self, username, token):
        """Look for an authorization based on token and username"""
        if len(token) < self.token_length or token == UNDEFINED_SECRET:
            return False
        if self.tokens_expire:
            now = datetime.datetime.utcnow()
        else:
            now = datetime.datetime.utcfromtimestamp(0)
        authz = self.db_session.query(OAuthAuthorization).filter(
            OAuthAuthorization.username == username,
            OAuthAuthorization.access_token == token,
            OAuthAuthorization.valid_until > now,
        ).first()
        user = self.db_session.query(UserProfile).filter(
            UserProfile.username == username
        ).first()
        return bool(authz) and not user.locked and not user.admin_disabled
