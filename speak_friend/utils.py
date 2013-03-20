def get_referrer(request):
    came_from = request.referrer
    if not came_from:
        came_from = '/'
    return came_from


def get_domain(request):
    referrer = get_referrer(request)
    path = request['PATH_INFO']
    if path == '/':
        domain = path
    else:
        domain = ''
    if referrer.endswith(path):
        domain = referrer[:-len(path)]
    return domain
