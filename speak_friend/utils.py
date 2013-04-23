from urlparse import urlsplit

from pyramid.interfaces import IRequest


def get_referrer(request):
    came_from = request.referrer
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


def remove_url_csrf(url):
    """Remove the CSRF token from a URL with GET parameters.
    """
    token_ident = '&csrf_token='
    start_index = url.find(token_ident)
    end_index = start_index + 40 + len(token_ident)
    url = url[:start_index] + url[end_index:]
    return url
