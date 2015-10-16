import string
from hashlib import sha256
from random import SystemRandom
from urllib import urlencode
from urlparse import parse_qsl, urlsplit, urlunsplit

from pyramid.interfaces import IRequest


UNICODE_ASCII_CHARACTERS = (string.ascii_letters.decode('ascii') +
    string.digits.decode('ascii'))


def get_referrer(request):
    came_from = request.session.get('came_from', request.referrer)
    if not came_from:
        came_from = '/'
    return came_from


def get_domain(request):
    if IRequest.providedBy(request):
        referrer = get_referrer(request)
    else:
        referrer = request
    if not referrer:
        return ''
    return urlsplit(referrer).netloc.split(':')[0]


def replace_url_csrf(url, session):
    """Replace the CSRF used in a GET form.
    """
    url_parts = urlsplit(url)
    query = url_parts.query
    query_dict = dict(parse_qsl(query))
    query_dict['csrf_token'] = session.get_csrf_token()
    query_string = urlencode(query_dict)
    url = urlunsplit([url_parts.scheme,
                   url_parts.netloc,
                   url_parts.path,
                   query_string,
                   url_parts.fragment]
    )
    return url


def get_xrds_url(request):
    if request.matchdict and 'username' in request.matchdict:
        username = request.matchdict['username']
        xrds_url = request.route_url('yadis_id',
                                               username=username)
    else:
        xrds_url = request.route_url('yadis')
    return xrds_url


def hash_string(original_str):
    """hash a string for database storage"""
    return sha256(original_str).hexdigest()


def random_ascii_string(length):
    random = SystemRandom()
    return ''.join([random.choice(UNICODE_ASCII_CHARACTERS) for x in xrange(length)])
