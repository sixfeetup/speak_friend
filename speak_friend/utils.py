def get_referrer(request):
    came_from = request.referrer
    if not came_from:
        came_from = '/'
    return came_from
