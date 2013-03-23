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
