from pyramid.renderers import render_to_response


def notfound(request):
    return render_to_response("speak_friend:templates/404_template.pt",
                              {},
                              request=request)


def notallowed(request):
    return render_to_response("speak_friend:templates/",
                              {},
                              request=request)
